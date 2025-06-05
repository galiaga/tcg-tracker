import { authFetch } from '../auth/auth.js';

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

const TagInputManager = (() => {
    let userTagsCache = []; 
    let isLoadingUserTags = false;
    let hasFetchedUserTags = false;

    async function fetchDefaultUserTags() {
        if (isLoadingUserTags) return userTagsCache;
        if (hasFetchedUserTags) return userTagsCache;
        isLoadingUserTags = true;
        try {
            const response = await authFetch("/api/tags");
            if (!response.ok) {
                throw new Error(`Failed to fetch tags: ${response.status}`);
            }
            userTagsCache = await response.json();
            userTagsCache.sort((a, b) => a.name.localeCompare(b.name));
            hasFetchedUserTags = true;
            return userTagsCache;
        } catch (error) {
            console.error("Error fetching default user tags:", error);
            hasFetchedUserTags = false; 
            return [];
        } finally {
            isLoadingUserTags = false;
        }
    }

    function handleSelection(selectedItemData, options) {
        const { inputElement, suggestionsElement, onTagAdded } = options;

        if (!selectedItemData || typeof selectedItemData.id === 'undefined' || typeof selectedItemData.name === 'undefined') {
            console.error("Invalid item data provided to handleSelection", selectedItemData);
            return;
        }

        if (typeof onTagAdded === 'function') {
            onTagAdded(selectedItemData); 
        }

        if (inputElement) inputElement.value = '';
        if (suggestionsElement) {
            suggestionsElement.innerHTML = '';
            suggestionsElement.style.display = 'none'; // Ensure 'hidden' class is used
        }
    }

    async function handleCreateNewRequest(itemName, options) {
        const { inputElement, suggestionsElement, onTagAdded, isCommanderSearch } = options;
        const normalizedItemName = itemName.trim();

        if (!normalizedItemName) return;

        if (isCommanderSearch) {
            console.warn("[TagInputManager] Attempted to create a commander. This is not supported here.");
            if (typeof showFlashMessage === 'function') showFlashMessage("Cannot create new commanders from this input.", "warning");
            if (inputElement) inputElement.value = '';
            if (suggestionsElement) suggestionsElement.style.display = 'none';
            return;
        }
        
        if (inputElement) inputElement.value = '';
        if (suggestionsElement) {
            suggestionsElement.innerHTML = '';
            suggestionsElement.style.display = 'none';
        }

        try {
            const response = await authFetch("/api/tags", {
                method: 'POST',
                body: JSON.stringify({ name: normalizedItemName })
            });

            if (!response) return; 
            const newItemData = await response.json();

            if (response.ok) {
                 if (!userTagsCache.some(t => t.id === newItemData.id)) {
                      userTagsCache.push(newItemData);
                      userTagsCache.sort((a, b) => a.name.localeCompare(b.name));
                 }
                 handleSelection(newItemData, options); 
            } else if (response.status === 409) {
                 const existingItem = newItemData.tag || userTagsCache.find(t => t.name.toLowerCase() === normalizedItemName.toLowerCase());
                 if (existingItem) {
                      handleSelection(existingItem, options); 
                 } else {
                      if (typeof showFlashMessage === 'function') showFlashMessage(newItemData.error || 'Item already exists but could not be retrieved.', 'warning');
                 }
            } else { 
                 console.error("Error creating item:", newItemData);
                 if (typeof showFlashMessage === 'function') showFlashMessage(newItemData.error || 'Failed to create item.', 'danger');
            }
        } catch(error) {
             console.error("API error creating item:", error);
             if (typeof showFlashMessage === 'function') showFlashMessage('Error connecting to server to create item.', 'danger');
        }
    }

    async function showSuggestions(options) {
        const { inputElement, suggestionsElement, searchFunction, renderSuggestionItem, isCommanderSearch } = options; 
        const inputValue = inputElement.value.trim();
        
        suggestionsElement.innerHTML = ''; 

        if (inputValue.length < 1) {
            suggestionsElement.classList.add('hidden');
            return;
        }

        let itemsToSuggest = [];
        if (typeof searchFunction === 'function') {
            try {
                itemsToSuggest = await searchFunction(inputValue);
            } catch (error) {
                console.error(`[TagInputManager] Error from provided searchFunction for ${inputElement.id}:`, error);
                itemsToSuggest = [];
            }
        } else {
            const currentTags = await fetchDefaultUserTags();
            const lowerInputValueForTags = inputValue.toLowerCase();
            itemsToSuggest = currentTags.filter(tag =>
                tag.name.toLowerCase().includes(lowerInputValueForTags)
            );
        }

        const suggestionsToShow = itemsToSuggest.slice(0, 10); 

        suggestionsToShow.forEach(item => {
            const suggestionElementWrapper = document.createElement('div'); 
            if (typeof renderSuggestionItem === 'function') {
                suggestionElementWrapper.innerHTML = renderSuggestionItem(item); 
                const clickableElement = suggestionElementWrapper.firstChild; 
                if (clickableElement) {
                    clickableElement.addEventListener('click', () => {
                        handleSelection(item, options);
                    });
                    suggestionsElement.appendChild(clickableElement);
                } else {
                     console.warn(`[TagInputManager] renderSuggestionItem for ${inputElement.id} did not produce a child element for item:`, item);
                }
            } else {
                const btn = document.createElement('button');
                btn.type = 'button';
                btn.className = 'w-full text-left block px-3 py-2 bg-violet-100 dark:bg-violet-700 text-violet-800 dark:text-violet-100 text-sm font-medium rounded-md hover:bg-violet-200 dark:hover:bg-violet-600 transition-colors duration-150 mb-1 focus:outline-none focus:ring-2 focus:ring-violet-500';
                btn.textContent = item.name;
                btn.addEventListener('click', () => {
                    handleSelection(item, options);
                });
                suggestionsElement.appendChild(btn);
            }
        });
        
        if (!isCommanderSearch && typeof searchFunction !== 'function') {
            const lowerInputValueForTags = inputValue.toLowerCase();
            let exactMatchFound = itemsToSuggest.some(tag => tag.name.toLowerCase() === lowerInputValueForTags);
            if (!exactMatchFound && inputValue) {
                const createBtn = document.createElement('button');
                createBtn.type = 'button';
                createBtn.className = 'w-full text-left block px-3 py-2 bg-green-100 dark:bg-green-700 text-green-700 dark:text-green-300 text-sm font-medium rounded-md hover:bg-green-200 dark:hover:bg-green-600 transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-green-500' + 
                                    (suggestionsToShow.length > 0 ? ' border-t border-gray-200 dark:border-gray-600 mt-2 pt-2' : '');
                createBtn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 inline-block mr-1.5 align-text-bottom" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" /></svg>Create: "${inputValue}"`;
                createBtn.addEventListener('click', () => {
                    handleCreateNewRequest(inputValue, options);
                });
                suggestionsElement.appendChild(createBtn);
            }
        }

        if (suggestionsElement.hasChildNodes()) {
            suggestionsElement.style.display = 'block';
        } else {
             if (inputValue) { 
                const noResults = document.createElement("li"); 
                noResults.className = "px-4 py-2 text-center text-sm text-gray-500 dark:text-gray-400";
                noResults.textContent = "No results found";
                suggestionsElement.appendChild(noResults);
                suggestionsElement.style.display = 'block';
            } else {
                suggestionsElement.style.display = 'none';
            }
        }
    }

    function initTagInput(options) {
        const { inputId, suggestionsId, onTagAdded, searchFunction, renderSuggestionItem, isCommanderSearch = false } = options; 
        const inputElement = document.getElementById(inputId);
        const suggestionsElement = document.getElementById(suggestionsId);


        if (!inputElement || !suggestionsElement) {
            console.error("TagInput init failed: Input or suggestions element not found.", { inputId, suggestionsId });
            return null; 
        }

        const instanceApi = {
            config: options,
            inputElement: inputElement,
            suggestionsElement: suggestionsElement,
            boundHideFunction: null, 
            handleInputEventRef: null,
            handleFocusEventRef: null,
            handleKeydownEventRef: null,
            clearInput: () => { 
                if (instanceApi.inputElement) instanceApi.inputElement.value = '';
                if (instanceApi.suggestionsElement) {
                    instanceApi.suggestionsElement.innerHTML = '';
                    instanceApi.suggestionsElement.style.display = 'none';
                }
            },
            destroy: () => { 
                instanceApi.inputElement?.removeEventListener('input', instanceApi.handleInputEventRef);
                instanceApi.inputElement?.removeEventListener('focus', instanceApi.handleFocusEventRef);
                instanceApi.inputElement?.removeEventListener('keydown', instanceApi.handleKeydownEventRef);

                if (instanceApi.boundHideFunction) {
                    document.removeEventListener('click', instanceApi.boundHideFunction); 
                    instanceApi.boundHideFunction = null; // Clear ref after removing
                }
            }
        };

        const instanceOptions = { 
            inputElement,
            suggestionsElement,
            onTagAdded,
            searchFunction, 
            renderSuggestionItem, 
            isCommanderSearch 
        };

        if (typeof searchFunction !== 'function' && !isCommanderSearch) {
            fetchDefaultUserTags(); 
        }
        
        const debouncedShowSuggestions = debounce(() => showSuggestions(instanceOptions), 300);

        instanceApi.handleInputEventRef = (event) => {
            debouncedShowSuggestions();
        };
        
        instanceApi.handleFocusEventRef = () => { 
            if (inputElement.value.trim().length > 0) {
                showSuggestions(instanceOptions); 
            }
        };

        instanceApi.handleKeydownEventRef = (event) => {
            if (event.key === 'Enter') {
                event.preventDefault();
                const firstSuggestionButtonOrItem = suggestionsElement.querySelector('button:not([disabled]), li:not([disabled])');
                const currentVal = inputElement.value.trim();

                if (!suggestionsElement.classList.contains('hidden') && firstSuggestionButtonOrItem) {
                     firstSuggestionButtonOrItem.click(); 
                } else if (currentVal && !isCommanderSearch && typeof searchFunction !== 'function') { 
                     handleCreateNewRequest(currentVal, instanceOptions);
                }
            } else if (event.key === 'Escape') {
                 suggestionsElement.classList.add('hidden');
            }
        };

        inputElement.addEventListener('input', instanceApi.handleInputEventRef);
        
        inputElement.addEventListener('focus', instanceApi.handleFocusEventRef);
        inputElement.addEventListener('keydown', instanceApi.handleKeydownEventRef);
        
        const hideFunc = (event) => {
            if (instanceApi.suggestionsElement && document.body.contains(instanceApi.suggestionsElement) &&
                instanceApi.inputElement && document.body.contains(instanceApi.inputElement)) {
                if (!instanceApi.inputElement.contains(event.target) && 
                    !instanceApi.suggestionsElement.contains(event.target)) {
                    if (instanceApi.suggestionsElement.style.display !== 'none') {
                         instanceApi.suggestionsElement.style.display = 'none';
                    }
                }
            } else if (instanceApi.boundHideFunction) { 
                document.removeEventListener('click', instanceApi.boundHideFunction);
                instanceApi.boundHideFunction = null; 
            }
        };
        instanceApi.boundHideFunction = hideFunc; 
        document.addEventListener('click', instanceApi.boundHideFunction); 

        return instanceApi; 
    }

    return {
        init: initTagInput,
        fetchAllUserTags: fetchDefaultUserTags 
    };

})();

export { TagInputManager };