import { authFetch } from '../../auth/auth.js';
import { sortAndRenderDecks } from './sort-decks.js';
import { openQuickAddTagModal, closeQuickAddTagModal } from '../tagUtils.js';

function getSelectedTagIds() {
    const optionsContainer = document.getElementById("tag-filter-options");
    const selectedIds = [];
    if (!optionsContainer) return selectedIds;
    const checkedBoxes = optionsContainer.querySelectorAll('input[type="checkbox"]:checked');
    checkedBoxes.forEach(checkbox => {
        if (checkbox.value && checkbox.value !== "") {
            selectedIds.push(checkbox.value);
        }
    });
    return selectedIds;
}

async function handleRemoveTagClick(event) {
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

async function updateDeckListView() {
    const sortSelect = document.getElementById("sort_decks");
    const formatSelect = document.getElementById("filter_decks");
    const decksContainer = document.getElementById('decks-container');
    if (!sortSelect || !formatSelect || !decksContainer) {
        console.error("Missing required elements for updating deck list view.");
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
    decksContainer.innerHTML = '<p class="text-center text-gray-500 col-span-full">Loading decks...</p>';
    try {
        const response = await authFetch(apiUrl);
        if (!response) throw new Error("Authentication or network error.");
        if (!response.ok) throw new Error(`API Error: ${response.status}`);
        const filteredDecks = await response.json();
        sortAndRenderDecks(filteredDecks || [], sortValue);
    } catch (error) {
        console.error("Error fetching or rendering decks:", error);
        if (typeof showFlashMessage === 'function') showFlashMessage("Error loading decks. " + error.message, "danger");
        if (decksContainer) decksContainer.innerHTML = '<p class="text-red-500 col-span-full">Error loading decks.</p>';
    }
}

export { updateDeckListView };

document.addEventListener('DOMContentLoaded', () => {
    const decksContainer = document.getElementById('decks-container');
    const sortSelect = document.getElementById("sort_decks");
    const formatSelect = document.getElementById("filter_decks");
    const tagFilterButton = document.getElementById("tag-filter-button");
    const tagFilterDropdown = document.getElementById("tag-filter-dropdown");
    const quickAddModal = document.getElementById("quickAddTagModal");
    const quickAddModalCloseBtn = document.getElementById("quickAddTagModalCloseButton");

    if (sortSelect && formatSelect && tagFilterButton && tagFilterDropdown && decksContainer && quickAddModal && quickAddModalCloseBtn)
    {
        updateDeckListView();
        decksContainer.addEventListener('click', handleRemoveTagClick);
        decksContainer.addEventListener('click', (event) => {
             const addButton = event.target.closest('.add-deck-tag-button');
             if (addButton) {
                 event.preventDefault();
                 event.stopPropagation();
                 const deckId = addButton.dataset.deckId;
                 if (deckId) {
                      openQuickAddTagModal(deckId, 'deck', updateDeckListView);
                 }
             }
        });

        quickAddModalCloseBtn.addEventListener('click', closeQuickAddTagModal);
        quickAddModal.addEventListener('click', (event) => {
            if (event.target === quickAddModal) {
                 closeQuickAddTagModal();
            }
        });

    } else {
         console.warn("Deck list manager could not initialize fully - required elements missing (sort, format, tag button/dropdown, container, or quick add modal).");
    }
});