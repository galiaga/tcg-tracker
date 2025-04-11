import { authFetch } from '../../auth/auth.js';
import { sortAndRenderDecks } from './sort-decks.js';
import { renderEmptyDecksMessage } from './deckCardComponent.js';
import { openQuickAddTagModal, closeQuickAddTagModal } from '../tag-utils.js';
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

export async function handleRemoveTagClick(event) {
    const removeButton = event.target.closest('.remove-tag-button');
    if (!removeButton) return;
    event.preventDefault();
    event.stopPropagation();
    const tagPill = removeButton.closest('.tag-pill');
    const cardElement = removeButton.closest('[data-deck-id]');
    if (!tagPill || !cardElement) return;
    const tagId = tagPill.dataset.tagId;
    const deckId = cardElement.dataset.deckId;
    if (!tagId || !deckId) {
        console.error("Could not find tagId or deckId for removal");
        if (typeof showFlashMessage === 'function') showFlashMessage("Could not remove tag: IDs missing.", "danger");
        return;
    }
    removeButton.disabled = true;
    tagPill.style.opacity = '0.5';
    try {
        const response = await authFetch(`/api/decks/${deckId}/tags/${tagId}`, { method: 'DELETE' });
        if (!response) throw new Error("Authentication or network error.");
        if (response.ok) {
             tagPill.remove();
             await populateTagFilter();
             await updateDeckListView();
        } else {
             const errorData = await response.json().catch(() => ({}));
             throw new Error(errorData.error || `Failed to remove tag (${response.status})`);
        }
    } catch (error) {
         console.error("Error removing tag:", error);
         if (typeof showFlashMessage === 'function') showFlashMessage(error.message || "Could not remove tag.", "danger");
         removeButton.disabled = false;
         tagPill.style.opacity = '1';
    }
}

function handleAddTagClick(event) {
    const addButton = event.target.closest('.add-deck-tag-button');
    if (addButton) {
        event.preventDefault();
        event.stopPropagation();
        const deckId = addButton.dataset.deckId;
        if (deckId) {
            const refreshAfterTagAdd = async () => {
                console.log("Refreshing tag filter dropdown and deck list after tag add...");
                try {
                    await populateTagFilter();
                    await updateDeckListView();
                    console.log("[deck-list-manager] refreshAfterTagAdd completed.");
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
        console.log("Initializing deck view: Populating tag filter...");
        try {
            await populateTagFilter(); 
            console.log("Tag filter populated. Updating deck list view...");
            await updateDeckListView(); 
            console.log("Deck list view updated.");
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