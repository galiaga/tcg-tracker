// backend/static/js/ui/decks/deck-list-manager.js

import { authFetch } from '../../auth/auth.js';
import { sortAndRenderDecks } from './sort-decks.js'; 
import { renderEmptyDecksMessage } from './deckCardComponent.js';
// Corrected import name: handleRemoveDeckTagClick
import { handleRemoveDeckTagClick, openQuickAddTagModal, closeQuickAddTagModal } from '../tag-utils.js'; 
import { populateTagFilter } from './filter-decks-by-tag.js';

// --- Helper Functions ---
function getSelectedTagIds() {
    const optionsContainer = document.getElementById("tag-filter-options");
    const selectedIds = [];
    if (!optionsContainer) return selectedIds;
    const checkedBoxes = optionsContainer.querySelectorAll('input[type="checkbox"]:checked');
    checkedBoxes.forEach(checkbox => {
        if (checkbox.value && checkbox.value !== "" && checkbox.id !== 'select-all-tags-checkbox') { 
            selectedIds.push(checkbox.value);
        }
    });
    return selectedIds;
}

// Function to find, scroll to, and highlight a newly created deck.
function highlightNewDeck() {
    const urlParams = new URLSearchParams(window.location.search);
    const newDeckId = urlParams.get('new_deck_id');

    // If the parameter isn't in the URL, do nothing.
    if (!newDeckId) {
        return;
    }

    // A small delay ensures the DOM has been updated by the rendering logic.
    setTimeout(() => {
        // Your deck cards must have a `data-deck-id` attribute for this to work.
        const newDeckCard = document.querySelector(`.deck-card[data-deck-id='${newDeckId}']`);
        
        if (newDeckCard) {
            // Scroll the new card into the middle of the viewport smoothly.
            newDeckCard.scrollIntoView({ behavior: 'smooth', block: 'center' });

            // Apply the initial highlight effect.
            newDeckCard.classList.add('new-deck-highlight');

            // After a moment, add the fade-out class to smoothly remove the highlight.
            setTimeout(() => {
                newDeckCard.classList.add('new-deck-highlight-fade-out');
                // Clean up the classes entirely after the transition is over.
                setTimeout(() => {
                    newDeckCard.classList.remove('new-deck-highlight', 'new-deck-highlight-fade-out');
                }, 600); // Must be slightly longer than the transition duration in CSS.
            }, 1500); // How long the highlight stays fully visible.
        }

        // Clean the URL in the browser's history so a refresh doesn't trigger the effect again.
        const newUrl = window.location.pathname;
        window.history.replaceState({}, document.title, newUrl);
    }, 200); // 200ms delay for robustness.
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

    const apiUrl = `/api/user_decks?${params.toString()}`; 
    decksContainer.innerHTML = '<div class="col-span-full p-6 text-center text-gray-500 dark:text-gray-400"><svg class="animate-spin h-8 w-8 text-violet-500 dark:text-violet-400 mx-auto mb-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>Loading decks...</div>';

    try {
        const response = await authFetch(apiUrl);
        if (!response) throw new Error("Authentication or network error occurred.");
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ error: `HTTP error ${response.status}` }));
            throw new Error(errorData.error || `API Error: ${response.status}`);
        }
        const fetchedDecks = await response.json();
        
        sortAndRenderDecks(fetchedDecks || [], sortValue, decksContainer, updateDeckListView);
    } catch (error) {
        console.error("Error fetching or rendering decks:", error);
        if (typeof showFlashMessage === 'function') { 
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
            if (event.target === quickAddModal) { 
                closeQuickAddTagModal();
            }
        });
    }
}


// --- DOMContentLoaded Initialization ---
document.addEventListener('DOMContentLoaded', () => {
    const decksContainer = document.getElementById('decks-container');
    const sortSelect = document.getElementById("sort_decks");
    const tagFilterButton = document.getElementById("tag-filter-button"); 
    const tagFilterDropdown = document.getElementById("tag-filter-dropdown"); 

    if (!decksContainer || !sortSelect || !tagFilterButton || !tagFilterDropdown ) {
         console.warn("Deck list manager could not initialize fully - one or more required elements are missing.");
         if (decksContainer && (!sortSelect || !tagFilterButton)) { 
            decksContainer.innerHTML = '<p class="text-red-500 dark:text-red-400 col-span-full p-4">Error: Cannot initialize deck sorting/filtering controls.</p>';
         }
         return;
    }

    initModalListeners(); 

    sortSelect.addEventListener('change', updateDeckListView);

    decksContainer.addEventListener('click', async (event) => {
        const removeButton = event.target.closest('.remove-deck-tag-button'); // Corrected class for deck cards
        if (removeButton) {
            event.preventDefault();
            event.stopPropagation();
            
            const tagPill = removeButton.closest('.tag-pill');
            const cardElement = removeButton.closest('[data-deck-id]'); // Ensure deck cards have data-deck-id
            const tagId = tagPill?.dataset.tagId;
            const deckId = cardElement?.dataset.deckId;

            if (deckId && tagId) {
                // Call the correctly imported function
                // The refreshCallback is updateDeckListView
                const success = await handleRemoveDeckTagClick(deckId, tagId, updateDeckListView, removeButton, tagPill);
                // No need to call updateDeckListView again if handleRemoveDeckTagClick calls its callback
            }
        }
        // Add tag button clicks are handled within renderDeckCard which calls openQuickAddTagModal
    });

    const initializeView = async () => {
        try {
            await populateTagFilter(updateDeckListView); 
            await updateDeckListView();
            highlightNewDeck();
        } catch (error) {
            console.error("Error during initial view initialization:", error);
             if (decksContainer) {
                 renderEmptyDecksMessage(decksContainer, "Error initializing view. Please refresh.");
             }
        }
    };
    initializeView();
});

export { updateDeckListView };