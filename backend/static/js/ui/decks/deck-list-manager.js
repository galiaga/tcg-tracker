// backend/static/js/ui/decks/deck-list-manager.js
import { authFetch } from '../../auth/auth.js';
import { sortAndRenderDecks } from './sort-decks.js'; // Assumes this handles rendering via renderDeckCard
import { renderEmptyDecksMessage } from './deckCardComponent.js';
import { handleRemoveTagClick, openQuickAddTagModal, closeQuickAddTagModal } from '../tag-utils.js';
import { populateTagFilter } from './filter-decks-by-tag.js';

// --- Helper Functions ---
function getSelectedTagIds() {
    const optionsContainer = document.getElementById("tag-filter-options");
    const selectedIds = [];
    if (!optionsContainer) return selectedIds;
    //This selector needs to be robust if the structure of tag options changes
    const checkedBoxes = optionsContainer.querySelectorAll('input[type="checkbox"]:checked');
    checkedBoxes.forEach(checkbox => {
        if (checkbox.value && checkbox.value !== "" && checkbox.id !== 'select-all-tags-checkbox') { // Exclude select-all
            selectedIds.push(checkbox.value);
        }
    });
    return selectedIds;
}

// --- Core View Update Function ---
async function updateDeckListView() {
    const sortSelect = document.getElementById("sort_decks");
    const decksContainer = document.getElementById('decks-container');

    if (!sortSelect || !decksContainer) {
        console.error("Missing required elements (sort select or decks container) for updating deck list view.");
        if (decksContainer) {
            decksContainer.innerHTML = '<p class="text-red-500 dark:text-red-400 col-span-full p-4">Error: UI elements missing. Cannot load decks.</p>';
        }
        return;
    }

    const sortValue = sortSelect.value;
    const selectedTagIds = getSelectedTagIds();
    const params = new URLSearchParams();
    if (selectedTagIds.length > 0) {
        params.append('tags', selectedTagIds.join(','));
    }
    // Add sort parameter to API if backend supports it, otherwise sorting is client-side
    // params.append('sort_by', sortValue); // Example if backend sorts

    const apiUrl = `/api/user_decks?${params.toString()}`; // Ensure this API endpoint exists and accepts 'tags' query param
    decksContainer.innerHTML = '<div class="col-span-full p-6 text-center text-gray-500 dark:text-gray-400"><svg class="animate-spin h-8 w-8 text-violet-500 dark:text-violet-400 mx-auto mb-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>Loading decks...</div>';

    try {
        const response = await authFetch(apiUrl);
        if (!response) throw new Error("Authentication or network error occurred.");
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ error: `HTTP error ${response.status}` }));
            throw new Error(errorData.error || `API Error: ${response.status}`);
        }
        const fetchedDecks = await response.json();
        
        // Pass `updateDeckListView` as the refresh callback to sortAndRenderDecks,
        // which will then pass it to renderDeckCard.
        sortAndRenderDecks(fetchedDecks || [], sortValue, decksContainer, updateDeckListView);
    } catch (error) {
        console.error("Error fetching or rendering decks:", error);
        if (typeof showFlashMessage === 'function') { // Ensure showFlashMessage is globally available
            showFlashMessage("Error loading decks: " + error.message, "danger");
        }
        renderEmptyDecksMessage(decksContainer, "Error loading decks. Please try again later.");
    }
}

// --- Modal Listeners ---
function initModalListeners() {
    const quickAddModal = document.getElementById('quickAddTagModal');
    const closeButton = document.getElementById('quickAddTagModalCloseButton');
    const doneButton = document.getElementById('quickAddTagModalDoneButton');

    if (closeButton) {
        closeButton.addEventListener('click', () => closeQuickAddTagModal());
    }
    if (doneButton) {
        doneButton.addEventListener('click', () => closeQuickAddTagModal());
    }
    if (quickAddModal) {
        quickAddModal.addEventListener('keydown', (event) => {
            if (event.key === 'Escape') {
                closeQuickAddTagModal();
            }
        });
        quickAddModal.addEventListener('click', (event) => {
            if (event.target === quickAddModal) { // Clicked on the backdrop itself
                closeQuickAddTagModal();
            }
        });
    }
}


// --- DOMContentLoaded Initialization ---
document.addEventListener('DOMContentLoaded', () => {
    const decksContainer = document.getElementById('decks-container');
    const sortSelect = document.getElementById("sort_decks");
    const tagFilterButton = document.getElementById("tag-filter-button"); // Used by filter-decks-by-tag.js
    const tagFilterDropdown = document.getElementById("tag-filter-dropdown"); // Used by filter-decks-by-tag.js

    if (!decksContainer || !sortSelect || !tagFilterButton || !tagFilterDropdown ) {
         console.warn("Deck list manager could not initialize fully - one or more required elements are missing.");
         if (decksContainer && (!sortSelect || !tagFilterButton)) { // Adjusted condition
            decksContainer.innerHTML = '<p class="text-red-500 dark:text-red-400 col-span-full p-4">Error: Cannot initialize deck sorting/filtering controls.</p>';
         }
         return;
    }

    initModalListeners(); // Initialize listeners for the Quick Add Tag modal

    sortSelect.addEventListener('change', updateDeckListView);

    // Event delegation for removing tags from deck cards
    decksContainer.addEventListener('click', async (event) => {
        const removeButton = event.target.closest('.remove-tag-button');
        if (removeButton) {
            event.preventDefault();
            event.stopPropagation();
            const removed = await handleRemoveTagClick(event); // handleRemoveTagClick needs to be robust
            if (removed) {
                // If handleRemoveTagClick doesn't refresh, or if a more immediate feedback is needed:
                await updateDeckListView(); // Refresh the list to show changes
            }
        }
        // Note: Add tag button clicks are handled within renderDeckCard
    });

    const initializeView = async () => {
        try {
            // populateTagFilter is expected to set up listeners for tag filter changes
            // that will eventually call updateDeckListView or a similar function.
            await populateTagFilter(updateDeckListView); // Pass callback if filter module needs it
            await updateDeckListView(); // Initial load of decks
        } catch (error) {
            console.error("Error during initial view initialization:", error);
             if (decksContainer) {
                 renderEmptyDecksMessage(decksContainer, "Error initializing view. Please refresh.");
             }
        }
    };
    initializeView();
});

// --- Exports ---
// updateDeckListView is the main function to refresh the view, can be called by other modules (e.g. filter)
export { updateDeckListView };