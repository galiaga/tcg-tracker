import { authFetch } from '../../auth/auth.js';
import { sortAndRenderDecks } from './sort-decks.js';
import { renderEmptyDecksMessage } from './deckCardComponent.js';
import { openQuickAddTagModal, closeQuickAddTagModal, handleRemoveTagClick } from '../tag-utils.js';
import { populateTagFilter } from './filter-decks-by-tag.js'; 

function getSelectedTagIds() {
    const optionsContainer = document.getElementById("tag-filter-options");
    const selectedIds = [];
    if (!optionsContainer) return selectedIds;
    const checkedBoxes = optionsContainer.querySelectorAll(':scope > div > input[type="checkbox"]:checked, :scope > input[type="checkbox"]:checked'); 
    checkedBoxes.forEach(checkbox => {
        if (checkbox.value && checkbox.value !== "") {
            selectedIds.push(checkbox.value);
        }
    });
    return selectedIds;
}

function handleAddTagClick(event) {
    const addButton = event.target.closest('.add-deck-tag-button');
    if (addButton) {
        event.preventDefault();
        event.stopPropagation();
        const deckId = addButton.dataset.deckId;
        if (deckId) {
            const refreshAfterTagAdd = async () => {
                try {
                    await populateTagFilter();
                    await updateDeckListView();
                } catch (error) {
                    console.error("Error during refresh after tag add:", error);
                    if (typeof showFlashMessage === 'function') {
                        showFlashMessage("Error refreshing lists after adding tag.", "danger");
                    }
                }
            };
            openQuickAddTagModal(deckId, 'deck', refreshAfterTagAdd);
        }
    }
}

async function updateDeckListView() {
    const sortSelect = document.getElementById("sort_decks");
    const formatSelect = document.getElementById("filter_decks");
    const decksContainer = document.getElementById('decks-container');

    if (!sortSelect || !formatSelect || !decksContainer) {
        console.error("Missing required elements (sort, format, or container) for updating deck list view.");
        if (decksContainer) {
            decksContainer.innerHTML = '<p class="text-red-500 col-span-full p-4">Error: UI elements missing. Cannot load decks.</p>';
        }
        return;
    }

    const sortValue = sortSelect.value;
    const formatValue = formatSelect.value;
    const selectedTagIds = getSelectedTagIds(); 

    const params = new URLSearchParams();
    if (formatValue && formatValue !== '0' && formatValue.toLowerCase() !== 'all') {
        params.append('deck_type_id', formatValue);
    }
    if (selectedTagIds.length > 0) {
        params.append('tags', selectedTagIds.join(','));
    }

    const apiUrl = `/api/user_decks?${params.toString()}`;
    decksContainer.innerHTML = '<p class="text-center text-violet-500 col-span-full p-4">Loading decks...</p>';

    try {
        const response = await authFetch(apiUrl);
        if (!response) throw new Error("Authentication or network error occurred.");
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ error: `HTTP error ${response.status}` }));
            throw new Error(errorData.error || `API Error: ${response.status}`);
        }
        const filteredDecks = await response.json();
        sortAndRenderDecks(filteredDecks || [], sortValue, decksContainer);
    } catch (error) {
        console.error("Error fetching or rendering decks:", error);
        if (typeof showFlashMessage === 'function') {
            showFlashMessage("Error loading decks: " + error.message, "danger");
        }
        renderEmptyDecksMessage(decksContainer, "Error loading decks. Please try again later.");
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const decksContainer = document.getElementById('decks-container');
    const sortSelect = document.getElementById("sort_decks");
    const formatSelect = document.getElementById("filter_decks");
    const tagFilterButton = document.getElementById("tag-filter-button");
    const tagFilterDropdown = document.getElementById("tag-filter-dropdown");
    const quickAddModal = document.getElementById("quickAddTagModal");
    const quickAddModalCloseBtn = document.getElementById("quickAddTagModalCloseButton");

    if (!decksContainer || !sortSelect || !formatSelect || !tagFilterButton || !tagFilterDropdown || !quickAddModal || !quickAddModalCloseBtn) {
         console.warn("Deck list manager could not initialize fully - one or more required elements are missing.");
         if (decksContainer && (!sortSelect || !formatSelect)) {
            decksContainer.innerHTML = '<p class="text-red-500 col-span-full p-4">Error: Cannot initialize deck sorting/filtering.</p>';
         }
         return;
    }

    sortSelect.addEventListener('change', updateDeckListView);
    formatSelect.addEventListener('change', updateDeckListView);
    decksContainer.addEventListener('click', handleRemoveTagClick);
    decksContainer.addEventListener('click', handleAddTagClick); 
    quickAddModalCloseBtn.addEventListener('click', closeQuickAddTagModal);
    quickAddModal.addEventListener('click', (event) => {
        if (event.target === quickAddModal) {
             closeQuickAddTagModal();
        }
    });

    const initializeView = async () => {
        try {
            await populateTagFilter(); 
            await updateDeckListView(); 
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