// backend/static/js/ui/decks/new-deck-modal.js

import { loadDeckTypes } from '../../deck_types.js'; // This seems to be for a removed deck_type select
import { conditionalFieldPrefixes, FIELD_CONFIG } from './deck-form.js';
import { TagInputManager } from '../tagInput.js'; // Using the older version

document.addEventListener("DOMContentLoaded", () => {
    const modal = document.getElementById("newDeckModal");
    if (!modal) {
        console.error("[new-deck-modal.js] New Deck Modal element not found.");
        return;
    }

    const modalContent = modal.querySelector(".bg-white, .dark\\:bg-gray-800"); // More robust selector
    const openBtn = document.getElementById("newDeckModalButton");
    const closeBtn = document.getElementById("newDeckModalCloseButton");
    const form = document.getElementById('register-deck-form');

    if (!modalContent || !openBtn || !closeBtn || !form) {
        console.error("[new-deck-modal.js] One or more critical modal elements (content, open/close buttons, form) not found.");
        return;
    }

    // --- Tag Input Management for New Deck Form ---
    let newDeckTagInputInstance = null; // Instance for this modal's tag input
    let selectedTagsForNewDeck = []; // Array to hold {id, name} of tags for the new deck

    // IDs from your my-decks.html for the new deck form's tag input
    const newDeckTagInputFieldId = 'deck-tags-input-field';
    const newDeckTagSuggestionsId = 'deck-tags-suggestions';
    // The older TagInputManager doesn't use these for pills in the input, but your HTML might have them for styling.
    // const newDeckTagWrapperId = 'deck-tags-input-wrapper'; 
    // const newDeckTagContainerId = 'deck-tags-container'; // This is where pills ARE displayed in your HTML

    function initializeTagInputForNewDeck() {
        if (typeof TagInputManager !== 'undefined' && TagInputManager.init) {
            if (newDeckTagInputInstance && typeof newDeckTagInputInstance.destroy === 'function') {
                newDeckTagInputInstance.destroy();
            }
            
            newDeckTagInputInstance = TagInputManager.init({
                inputId: newDeckTagInputFieldId,
                suggestionsId: newDeckTagSuggestionsId,
                onTagAdded: (tagData) => {
                    // This callback is triggered when a tag is selected/created
                    // Add it to our local array and update the UI to show the pill
                    if (!selectedTagsForNewDeck.some(t => t.id === tagData.id)) {
                        selectedTagsForNewDeck.push(tagData);
                        renderNewDeckTagPill(tagData); // Function to display the pill
                    }
                    // The older TagInputManager clears its own input after onTagAdded
                }
            });

            if (newDeckTagInputInstance && typeof newDeckTagInputInstance.clearInput === 'function') {
                // form.tagInputInstance = newDeckTagInputInstance; // Not strictly needed to attach to form
                newDeckTagInputInstance.clearInput(); // Clear the text input field
            } else if (!newDeckTagInputInstance) {
                console.error("[new-deck-modal.js] Failed to initialize TagInputManager for new deck modal.");
            }
        } else {
            console.warn("[new-deck-modal.js] TagInputManager not loaded or init function missing.");
        }
    }

    // Function to render a tag pill in the new deck form's tag area
    function renderNewDeckTagPill(tagData) {
        const container = document.getElementById('deck-tags-container'); // Your HTML has this for pills
        if (!container) {
            console.error("[new-deck-modal.js] 'deck-tags-container' not found for rendering pill.");
            return;
        }

        const pill = document.createElement('span');
        // Using styling similar to your deck cards for consistency
        pill.className = 'tag-pill inline-flex items-center whitespace-nowrap bg-violet-100 dark:bg-violet-700/60 px-2.5 py-1 text-xs font-semibold text-violet-700 dark:text-violet-200 rounded-full';
        pill.dataset.tagId = tagData.id;

        const tagNameSpan = document.createElement('span');
        tagNameSpan.textContent = tagData.name;
        pill.appendChild(tagNameSpan);

        const removeBtn = document.createElement('button');
        removeBtn.type = 'button';
        removeBtn.className = 'remove-new-deck-tag-btn ml-1.5 -mr-0.5 flex-shrink-0 rounded-full p-0.5 text-violet-500 dark:text-violet-400 hover:bg-violet-200 dark:hover:bg-violet-600 focus:outline-none focus:ring-1 focus:ring-violet-400 dark:focus:ring-violet-500';
        removeBtn.innerHTML = `<svg class="h-2.5 w-2.5" stroke="currentColor" fill="none" viewBox="0 0 8 8"><path stroke-linecap="round" stroke-width="1.5" d="M1 1l6 6m0-6L1 7" /></svg>`;
        removeBtn.setAttribute('aria-label', `Remove ${tagData.name}`);

        removeBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            selectedTagsForNewDeck = selectedTagsForNewDeck.filter(t => t.id !== tagData.id);
            pill.remove();
            const inputField = document.getElementById(newDeckTagInputFieldId);
            if (inputField) inputField.focus();
        });

        pill.appendChild(removeBtn);
        container.appendChild(pill); // Append before the input field if structure allows, or just into the container
    }

    function clearDisplayedNewDeckTags() {
        selectedTagsForNewDeck = []; // Clear the array
        const container = document.getElementById('deck-tags-container');
        if (container) {
            container.innerHTML = ''; // Clear displayed pills
        }
        if (newDeckTagInputInstance && typeof newDeckTagInputInstance.clearInput === 'function') {
            newDeckTagInputInstance.clearInput(); // Clear the text input field itself
        } else { // Fallback if instance is not available
            const tagInput = document.getElementById(newDeckTagInputFieldId);
            if (tagInput) tagInput.value = '';
        }
    }

    // --- Reset Logic ---
    function resetNewDeckForm() {
        if (form) form.reset();

        // loadDeckTypes might be for a select that was removed. If not needed, remove the call.
        // If it's for something else, ensure it's still relevant.
        // loadDeckTypes(); 

        conditionalFieldPrefixes.forEach(prefix => {
            const config = FIELD_CONFIG[prefix];
            if (!config) return;

            const fieldDiv = document.getElementById(config.fieldId);
            const inputElement = document.getElementById(config.inputId);
            const suggestionsUl = document.getElementById(config.suggestionsId);

            if (fieldDiv) {
                if (prefix !== 'commander') { 
                    fieldDiv.style.display = 'none';
                } else {
                    fieldDiv.style.display = 'block'; 
                }
            }
            if (inputElement) {
                 const datasetKey = config.datasetKey;
                 if (inputElement.dataset[datasetKey]) {
                     delete inputElement.dataset[datasetKey];
                 }
                 inputElement.value = '';
            }
            if (suggestionsUl) {
                suggestionsUl.innerHTML = '';
                suggestionsUl.style.display = 'none';
            }
        });
        clearDisplayedNewDeckTags(); // Clear tags and the selectedTagsForNewDeck array
    }

    // --- Modal Lifecycle ---
    function openModal() {
        modal.classList.remove("hidden");
        modal.classList.add("flex");

        // loadDeckTypes(); // Call this if it's still needed for the form
        resetNewDeckForm();       // Reset form state (includes clearing tags)
        initializeTagInputForNewDeck(); // Initialize/Re-initialize tag input

        setTimeout(() => {
            if (modalContent) {
                modalContent.classList.remove("scale-95", "opacity-0");
                modalContent.classList.add("scale-100", "opacity-100");
            }
        }, 10);
    }

    function closeModal() {
        if (modalContent) {
            modalContent.classList.remove("scale-100", "opacity-100");
            modalContent.classList.add("scale-95", "opacity-0");
        }

        setTimeout(() => {
            modal.classList.add("hidden");
            modal.classList.remove("flex");
            resetNewDeckForm(); // Clean up for next time
            if (newDeckTagInputInstance && typeof newDeckTagInputInstance.destroy === 'function') {
                newDeckTagInputInstance.destroy(); // Destroy TagInput instance
                newDeckTagInputInstance = null;
            }
        }, 150);
    }

    // --- Event Listeners ---
    if (openBtn) openBtn.addEventListener("click", openModal);
    if (closeBtn) closeBtn.addEventListener("click", closeModal);

    modal.addEventListener("click", (event) => {
        if (event.target === modal) {
            closeModal();
        }
    });

    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && !modal.classList.contains('hidden')) {
            closeModal();
        }
    });

    // The actual form submission is handled by registerDeck.js, which will need
    // to access `selectedTagsForNewDeck` or get the tag IDs from the rendered pills.
    // Exposing it or making it accessible to registerDeck.js is one way.
    // For example, registerDeck.js could read from `document.getElementById('deck-tags-container').querySelectorAll('[data-tag-id]')`
    // Or we can attach `selectedTagsForNewDeck` to the form element.
    if (form) {
        form.getSelectedTagsForNewDeck = () => selectedTagsForNewDeck.map(tag => tag.id);
    }

});