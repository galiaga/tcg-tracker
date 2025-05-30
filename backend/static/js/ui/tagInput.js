import { authFetch } from '../auth/auth.js';

const TagInputManager = (() => {
    let userTags = [];
    let isLoading = false;
    let hasFetched = false;

    async function fetchUserTags() {
        if (isLoading || hasFetched) return userTags;
        isLoading = true;
        try {
            const response = await authFetch("/api/tags");
            if (!response.ok) {
                throw new Error(`Failed to fetch tags: ${response.status}`);
            }
            userTags = await response.json();
            userTags.sort((a, b) => a.name.localeCompare(b.name));
            hasFetched = true;
            return userTags;
        } catch (error) {
            console.error("Error fetching user tags:", error);
            hasFetched = false;
            return [];
        } finally {
            isLoading = false;
        }
    }

    function renderTagPill(tagData, options) {
        const { containerElement, inputElement, suggestionsElement, selectedTags, onTagAdded } = options;

        if (!tagData || typeof tagData.id === 'undefined' || typeof tagData.name === 'undefined') {
            console.error("Invalid tag data provided to renderTagPill", tagData);
            return;
        }

        if (selectedTags.some(t => t.id === tagData.id)) {
            inputElement.value = '';
            suggestionsElement.innerHTML = '';
            suggestionsElement.classList.add('hidden');
            return;
        }

        selectedTags.push(tagData);

        const pill = document.createElement('span');
        pill.className = 'inline-flex items-center gap-1 bg-violet-100 text-violet-800 text-xs font-medium px-2 py-0.5 rounded-md mr-1 mb-1';
        pill.dataset.tagId = tagData.id;
        pill.textContent = tagData.name;

        const removeBtn = document.createElement('button');
        removeBtn.type = 'button';
        removeBtn.className = 'ml-0.5 text-violet-600 hover:text-violet-800 font-bold focus:outline-none';
        removeBtn.innerHTML = '&times;';
        removeBtn.ariaLabel = `Remove ${tagData.name}`;

        removeBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            const index = selectedTags.findIndex(t => t.id === tagData.id);
            if (index > -1) {
                selectedTags.splice(index, 1);
            }
            pill.remove();
        });

        pill.appendChild(removeBtn);

        containerElement.appendChild(pill);

        if (typeof onTagAdded === 'function') {
            onTagAdded(tagData);
        }

        inputElement.value = '';
        suggestionsElement.innerHTML = '';
        suggestionsElement.classList.add('hidden');
        inputElement.focus();
    }

    async function handleCreateTag(tagName, options) {
        const { inputElement, suggestionsElement } = options;
        const normalizedTagName = tagName.trim().toLowerCase();

        if (!normalizedTagName) return;

        inputElement.value = '';
        suggestionsElement.innerHTML = '';
        suggestionsElement.classList.add('hidden');

        try {
            const response = await authFetch("/api/tags", {
                method: 'POST',
                body: JSON.stringify({ name: normalizedTagName })
            });

            if (!response) return;

            const newTagData = await response.json();

            if (response.ok) {
                 if (!userTags.some(t => t.id === newTagData.id)) {
                      userTags.push(newTagData);
                      userTags.sort((a, b) => a.name.localeCompare(b.name));
                 }
                 renderTagPill(newTagData, options);
            } else if (response.status === 409) {
                 const existingTag = userTags.find(t => t.name === normalizedTagName);
                 if (existingTag) {
                      renderTagPill(existingTag, options);
                 } else {
                      if (typeof showFlashMessage === 'function') {
                           showFlashMessage(newTagData.error || 'Tag already exists.', 'warning');
                       }
                 }
            } else {
                 console.error("Error creating tag:", newTagData);
                 if (typeof showFlashMessage === 'function') {
                      showFlashMessage(newTagData.error || 'Failed to create tag.', 'danger');
                 }
            }
        } catch(error) {
             console.error("API error creating tag:", error);
             if (typeof showFlashMessage === 'function') {
                  showFlashMessage('Error connecting to server to create tag.', 'danger');
             }
        }
    }


    function showSuggestions(options) {
        const { inputElement, suggestionsElement, selectedTags } = options;
        const inputValue = inputElement.value.trim();
        const lowerInputValue = inputValue.toLowerCase();

        suggestionsElement.innerHTML = '';

        if (inputValue.length < 1) {
            suggestionsElement.classList.add('hidden');
            return;
        }

        const filteredTags = userTags.filter(tag =>
            tag.name.toLowerCase().includes(lowerInputValue) &&
            !selectedTags.some(st => st.id === tag.id)
        );

        let exactMatchFound = userTags.some(tag => tag.name.toLowerCase() === lowerInputValue);

        const suggestionsToShow = filteredTags.slice(0, 10);

        suggestionsToShow.forEach(tag => {
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'w-full text-left block px-3 py-1.5 bg-violet-100 text-violet-800 text-xs font-medium rounded-md hover:bg-violet-200 transition-colors duration-150 mb-1 focus:outline-none focus:ring-2 focus:ring-violet-300';
            btn.textContent = tag.name;
            btn.dataset.id = tag.id;
            btn.dataset.name = tag.name;

            btn.addEventListener('click', () => {
                renderTagPill({ id: tag.id, name: tag.name }, options);
            });
            suggestionsElement.appendChild(btn);
        });

        if (!exactMatchFound && inputValue) {
            const createBtn = document.createElement('button');
            createBtn.type = 'button';
            createBtn.className = 'w-full text-left block px-3 py-1.5 bg-green-100 text-green-700 text-xs font-medium rounded-md hover:bg-green-200 transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-green-300' + (suggestionsToShow.length > 0 ? ' border-t border-gray-200 mt-2 pt-2' : '');
            createBtn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3 inline-block mr-1 align-middle" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3"><path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" /></svg>Create: "${inputValue}"`;

            createBtn.addEventListener('click', () => {
                handleCreateTag(inputValue, options);
            });
            suggestionsElement.appendChild(createBtn);
        }


        if (suggestionsElement.hasChildNodes()) {
            suggestionsElement.classList.remove('hidden');
        } else {
            suggestionsElement.classList.add('hidden');
        }
    }


    function initTagInput(options) {
        const { inputId, suggestionsId, containerId, onTagAdded } = options;
        const inputElement = document.getElementById(inputId);
        const suggestionsElement = document.getElementById(suggestionsId);
        const containerElement = document.getElementById(containerId);

        if (!inputElement || !suggestionsElement || !containerElement) {
            console.error("TagInput init failed: One or more elements not found.", options);
            return null;
        }

        let selectedTags = [];

        const instanceOptions = {
            inputElement,
            suggestionsElement,
            containerElement,
            selectedTags,
            onTagAdded
        };

        if (!hasFetched) {
             fetchUserTags();
        } else {
            suggestionsElement.innerHTML = '';
            suggestionsElement.classList.add('hidden');
        }

        inputElement.addEventListener('input', () => {
            showSuggestions(instanceOptions);
        });

        document.addEventListener('click', (event) => {
             if (!inputElement.contains(event.target) && !suggestionsElement.contains(event.target)) {
                 if (!suggestionsElement.classList.contains('hidden')) {
                      suggestionsElement.classList.add('hidden');
                 }
             }
         });

         inputElement.addEventListener('keydown', (event) => {
             if (event.key === 'Enter') {
                 event.preventDefault();
                 const firstSuggestion = suggestionsElement.querySelector('li');
                 const currentVal = inputElement.value.trim();
                 if (!suggestionsElement.classList.contains('hidden') && firstSuggestion) {
                      firstSuggestion.click();
                 } else if (currentVal) {
                      handleCreateTag(currentVal, instanceOptions);
                 }
             } else if (event.key === 'Backspace' && inputElement.value === '' && selectedTags.length > 0) {
                 const lastPill = containerElement.querySelector('span:last-child[data-tag-id]'); 
                 if (lastPill) {
                      const lastTagId = parseInt(lastPill.dataset.tagId, 10);
                      const index = selectedTags.findIndex(t => t.id === lastTagId);
                      if (index > -1) {
                           selectedTags.splice(index, 1);
                      }
                      lastPill.remove();
                 }
             } else if (event.key === 'Escape') {
                  suggestionsElement.classList.add('hidden');
             }
         });

         inputElement.addEventListener('focus', () => {
         });

        return {
            getSelectedTagIds: () => selectedTags.map(tag => tag.id),
            addTag: (tagData) => renderTagPill(tagData, instanceOptions),
            clearTags: () => {
                containerElement.innerHTML = '';
                selectedTags.length = 0;
            }
        };
    }

    return {
        init: initTagInput
    };

})();

export { TagInputManager };