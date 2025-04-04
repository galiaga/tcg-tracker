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
        const { containerElement, inputElement, suggestionsElement, selectedTags } = options;

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
        pill.className = 'inline-flex items-center gap-1 bg-blue-100 text-blue-700 text-sm font-medium px-2.5 py-0.5 rounded-full';
        pill.dataset.tagId = tagData.id;
        pill.textContent = tagData.name;

        const removeBtn = document.createElement('button');
        removeBtn.type = 'button';
        removeBtn.className = 'ml-1 text-blue-500 hover:text-blue-700 font-bold focus:outline-none';
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
                 if (typeof showFlashMessage === 'function') {
                     showFlashMessage(`Tag "${newTagData.name}" created and added.`, 'success');
                 }
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
        const { inputElement, suggestionsElement, containerElement, selectedTags } = options;
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

        if (filteredTags.length === 0 && !exactMatchFound) {
             const li = document.createElement('li');
             li.className = 'px-3 py-2 cursor-pointer hover:bg-green-100 text-sm text-green-700';
             li.textContent = `Create new tag: "${inputValue}"`;
             li.addEventListener('click', () => {
                  handleCreateTag(inputValue, options);
             });
             suggestionsElement.appendChild(li);

        } else {
             filteredTags.slice(0, 10).forEach(tag => {
                 const li = document.createElement('li');
                 li.className = 'px-3 py-2 cursor-pointer hover:bg-gray-100 text-sm';
                 li.textContent = tag.name;
                 li.dataset.id = tag.id;
                 li.dataset.name = tag.name;
                 li.addEventListener('click', () => {
                      renderTagPill({ id: tag.id, name: tag.name }, options);
                 });
                 suggestionsElement.appendChild(li);
             });

             if (!exactMatchFound && inputValue) {
                  const createLi = document.createElement('li');
                  createLi.className = 'px-3 py-2 cursor-pointer hover:bg-green-100 text-sm text-green-700 border-t border-gray-100';
                  createLi.textContent = `Create new tag: "${inputValue}"`;
                  createLi.addEventListener('click', () => {
                       handleCreateTag(inputValue, options);
                  });
                  suggestionsElement.appendChild(createLi);
             }
        }

        if (suggestionsElement.hasChildNodes()) {
             suggestionsElement.classList.remove('hidden');
        } else {
             suggestionsElement.classList.add('hidden');
        }
    }


    function initTagInput(options) {
        const { inputId, suggestionsId, containerId } = options;
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
            selectedTags
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
                 const lastPill = containerElement.querySelector('span:last-child');
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