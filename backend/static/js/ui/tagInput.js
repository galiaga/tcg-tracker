// backend/static/js/ui/tagInput.js
import { authFetch } from '../auth/auth.js';

const TagInputManager = (() => {
    let userTags = []; // Global cache for all user tags
    let isLoading = false;
    let hasFetched = false;

    async function fetchUserTags() {
        if (isLoading) return userTags; // If already loading, let it finish
        if (hasFetched) return userTags; // Return cached if already fetched
        isLoading = true;
        try {
            const response = await authFetch("/api/tags");
            if (!response.ok) {
                // console.error(`Failed to fetch tags: ${response.status}`);
                throw new Error(`Failed to fetch tags: ${response.status}`);
            }
            userTags = await response.json();
            userTags.sort((a, b) => a.name.localeCompare(b.name)); // Sort once fetched
            hasFetched = true;
            return userTags;
        } catch (error) {
            console.error("Error fetching user tags:", error);
            hasFetched = false; // Allow retry on next init
            return []; // Return empty on error
        } finally {
            isLoading = false;
        }
    }

    // This function is effectively the "select tag" or "confirm tag" action
    function handleTagSelection(tagData, options) {
        const { inputElement, suggestionsElement, onTagAdded } = options;

        if (!tagData || typeof tagData.id === 'undefined' || typeof tagData.name === 'undefined') {
            console.error("Invalid tag data provided to handleTagSelection", tagData);
            return;
        }

        // Call the provided callback when a tag is selected or created
        if (typeof onTagAdded === 'function') {
            onTagAdded(tagData); // This will trigger associateTag in tag-utils.js
        }

        // Clear input and hide suggestions
        if (inputElement) inputElement.value = '';
        if (suggestionsElement) {
            suggestionsElement.innerHTML = '';
            suggestionsElement.classList.add('hidden');
        }
        if (inputElement) inputElement.focus();
    }

    async function handleCreateTagRequest(tagName, options) {
        const { inputElement, suggestionsElement } = options;
        const normalizedTagName = tagName.trim(); // Keep original case for creation, backend can normalize

        if (!normalizedTagName) return;

        // Clear input and hide suggestions immediately
        if (inputElement) inputElement.value = '';
        if (suggestionsElement) {
            suggestionsElement.innerHTML = '';
            suggestionsElement.classList.add('hidden');
        }
        
        try {
            const response = await authFetch("/api/tags", {
                method: 'POST',
                body: JSON.stringify({ name: normalizedTagName }) // Send original case
            });

            if (!response) return; // authFetch handles CSRF by returning null

            const newTagData = await response.json();

            if (response.ok) { // Tag created successfully (201)
                 // Update global cache if it's a truly new tag
                 if (!userTags.some(t => t.id === newTagData.id)) {
                      userTags.push(newTagData);
                      userTags.sort((a, b) => a.name.localeCompare(b.name));
                 }
                 handleTagSelection(newTagData, options); // Process the newly created tag
            } else if (response.status === 409) { // Conflict - tag name exists
                 // The backend should return the existing tag data in the 409 response
                 const existingTag = newTagData.tag || userTags.find(t => t.name.toLowerCase() === normalizedTagName.toLowerCase());
                 if (existingTag) {
                      handleTagSelection(existingTag, options); // Process the existing tag
                 } else {
                      if (typeof showFlashMessage === 'function') {
                           showFlashMessage(newTagData.error || 'Tag already exists but could not be retrieved.', 'warning');
                       }
                 }
            } else { // Other errors
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

    async function showSuggestions(options) { // Changed to async as fetchUserTags is async
        const { inputElement, suggestionsElement } = options;
        const inputValue = inputElement.value.trim();
        const lowerInputValue = inputValue.toLowerCase();

        suggestionsElement.innerHTML = ''; // Clear previous suggestions

        if (inputValue.length < 1) {
            suggestionsElement.classList.add('hidden');
            return;
        }

        // Ensure tags are fetched before filtering
        const currentTags = await fetchUserTags(); // Use the global cache

        const filteredTags = currentTags.filter(tag =>
            tag.name.toLowerCase().includes(lowerInputValue)
            // No need to filter selectedTags as this version doesn't maintain a selectedTags list in the UI
        );

        // Check if an exact match (case-insensitive) already exists in the fetched tags
        let exactMatchFound = currentTags.some(tag => tag.name.toLowerCase() === lowerInputValue);

        const suggestionsToShow = filteredTags.slice(0, 10); // Limit suggestions

        suggestionsToShow.forEach(tag => {
            const btn = document.createElement('button');
            btn.type = 'button';
            // Styling from your screenshot
            btn.className = 'w-full text-left block px-3 py-2 bg-violet-100 dark:bg-violet-700 text-violet-800 dark:text-violet-100 text-sm font-medium rounded-md hover:bg-violet-200 dark:hover:bg-violet-600 transition-colors duration-150 mb-1 focus:outline-none focus:ring-2 focus:ring-violet-500';
            btn.textContent = tag.name;
            // No dataset needed here as we pass the full tag object
            btn.addEventListener('click', () => {
                handleTagSelection({ id: tag.id, name: tag.name }, options);
            });
            suggestionsElement.appendChild(btn);
        });

        // "Create new tag" button
        if (!exactMatchFound && inputValue) {
            const createBtn = document.createElement('button');
            createBtn.type = 'button';
            // Styling from your screenshot
            createBtn.className = 'w-full text-left block px-3 py-2 bg-green-100 dark:bg-green-700 text-green-700 dark:text-green-300 text-sm font-medium rounded-md hover:bg-green-200 dark:hover:bg-green-600 transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-green-500' + 
                                (suggestionsToShow.length > 0 ? ' border-t border-gray-200 dark:border-gray-600 mt-2 pt-2' : '');
            createBtn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 inline-block mr-1.5 align-text-bottom" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" /></svg>Create: "${inputValue}"`;

            createBtn.addEventListener('click', () => {
                handleCreateTagRequest(inputValue, options);
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
        // This older version does not use `containerId` for pills,
        // it uses `suggestionsId` for the dropdown.
        // `onTagAdded` is the crucial callback.
        const { inputId, suggestionsId, onTagAdded } = options; 
        const inputElement = document.getElementById(inputId);
        const suggestionsElement = document.getElementById(suggestionsId);
        // No containerElement for pills in this version's input field itself.

        if (!inputElement || !suggestionsElement) {
            console.error("TagInput init failed: Input or suggestions element not found.", { inputId, suggestionsId });
            return null; // Return null if essential elements are missing
        }

        // This version doesn't maintain a `selectedTags` array within the input UI itself.
        // The `onTagAdded` callback handles the "selected" tag immediately.
        const instanceOptions = {
            inputElement,
            suggestionsElement,
            onTagAdded // This is key
        };

        // Fetch tags if not already done. showSuggestions will await this.
        fetchUserTags(); 

        inputElement.addEventListener('input', () => {
            showSuggestions(instanceOptions);
        });
        
        inputElement.addEventListener('focus', () => { // Show suggestions on focus if there's input
            if (inputElement.value.trim().length > 0) {
                showSuggestions(instanceOptions);
            }
        });

        // Hide suggestions when clicking outside
        // A bound function for removal
        const boundHideSuggestionsOnClickOutside = (event) => {
            if (suggestionsElement && !inputElement.contains(event.target) && !suggestionsElement.contains(event.target)) {
                if (!suggestionsElement.classList.contains('hidden')) {
                     suggestionsElement.classList.add('hidden');
                }
            }
        };
        document.addEventListener('click', boundHideSuggestionsOnClickOutside);


         inputElement.addEventListener('keydown', (event) => {
             if (event.key === 'Enter') {
                 event.preventDefault();
                 // Try to click the first suggestion button if visible
                 const firstSuggestionButton = suggestionsElement.querySelector('button:not([disabled])');
                 const currentVal = inputElement.value.trim();

                 if (!suggestionsElement.classList.contains('hidden') && firstSuggestionButton) {
                      firstSuggestionButton.click(); // This will trigger handleTagSelection
                 } else if (currentVal) { // If no suggestions, but there's input, try to create
                      handleCreateTagRequest(currentVal, instanceOptions);
                 }
             } else if (event.key === 'Escape') {
                  suggestionsElement.classList.add('hidden');
             }
             // Backspace to remove pills is not applicable as there are no pills in this input style
         });
        
        // The returned object for this simpler version
        return {
            // No getSelectedTagIds or addTag needed as it doesn't manage pills in UI
            clearInput: () => { // Renamed from clearTags as it only clears the input field
                if (inputElement) inputElement.value = '';
                if (suggestionsElement) {
                    suggestionsElement.innerHTML = '';
                    suggestionsElement.classList.add('hidden');
                }
            },
            destroy: () => { // Important to remove document-level event listener
                document.removeEventListener('click', boundHideSuggestionsOnClickOutside);
                // console.log("Simplified TagInput instance destroyed for input:", inputId);
            }
        };
    }

    return {
        init: initTagInput,
        // Expose fetchUserTags if other parts of the app need to preload tags
        fetchAllUserTags: fetchUserTags 
    };

})();

export { TagInputManager };