import { authFetch } from '../../auth/auth.js';
import { sortAndRenderDecks } from './sort-decks.js';
import { TagInputManager } from '../tagInput.js';

let quickAddTagInputInstance = null;
let currentItemIdForTagging = null;

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

async function associateTag(itemType, itemId, tagData) {
      if (!itemId || !tagData || typeof tagData.id === 'undefined') {
          console.error("Missing item ID or tag data for association");
          return;
      }
      const tagId = tagData.id;
      const apiUrl = itemType === 'deck'
                   ? `/api/decks/${itemId}/tags`
                   : `/api/matches/${itemId}/tags`;
      try {
          const response = await authFetch(apiUrl, {
              method: 'POST',
              body: JSON.stringify({ tag_id: tagId })
          });
           if (!response) throw new Error("Auth/Network Error");

          if (response.ok) {
               if (typeof showFlashMessage === 'function') {
                   showFlashMessage(`Tag "${tagData.name}" added to ${itemType} ${itemId}.`, 'success', 2000);
               }
               closeQuickAddTagModal();
               updateDeckListView();
          } else {
               const errorData = await response.json().catch(() => ({}));
               throw new Error(errorData.error || `Failed to add tag (${response.status})`);
          }
      } catch (error) {
           console.error(`Error associating tag ${tagId} with ${itemType} ${itemId}:`, error);
           if (typeof showFlashMessage === 'function') {
                showFlashMessage(error.message || `Could not add tag.`, 'danger');
           }
           closeQuickAddTagModal();
      }
}


function openQuickAddTagModal(itemId, itemType = 'deck') {
    const modal = document.getElementById("quickAddTagModal");
    const modalContent = modal?.querySelector(".bg-white");
    const title = modal?.querySelector("#quickAddTagModalTitle");
    const tagInputElement = document.getElementById('quick-add-tag-input');

    if (!modal || !modalContent || !title || !tagInputElement) {
        console.error("Quick Add Tag Modal elements not found.");
        return;
    }

    currentItemIdForTagging = itemId;
    title.textContent = `Add Tag to ${itemType} #${itemId}`;

    if (typeof TagInputManager !== 'undefined') {
        quickAddTagInputInstance = TagInputManager.init({
             inputId: 'quick-add-tag-input',
             suggestionsId: 'quick-add-tags-suggestions',
             containerId: 'quick-add-tags-container',
             onTagAdded: (tagData) => {
                 associateTag(itemType, currentItemIdForTagging, tagData);
             }
        });
        if (quickAddTagInputInstance) {
             quickAddTagInputInstance.clearTags();
             setTimeout(() => tagInputElement.focus(), 50);
        }
    }

    modal.classList.remove("hidden");
    setTimeout(() => {
      modalContent.classList.remove("scale-95", "opacity-0");
      modalContent.classList.add("scale-100", "opacity-100");
    }, 10);
}

function closeQuickAddTagModal() {
    const modal = document.getElementById("quickAddTagModal");
    const modalContent = modal?.querySelector(".bg-white");
    if (!modal || !modalContent) return;

    if (quickAddTagInputInstance) {
         quickAddTagInputInstance.clearTags();
    }
    currentItemIdForTagging = null;

    modalContent.classList.remove("scale-100", "opacity-100");
    modalContent.classList.add("scale-95", "opacity-0");
    setTimeout(() => {
        modal.classList.add("hidden");
    }, 150);
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
        if (typeof showFlashMessage === 'function') {
            showFlashMessage("Could not remove tag: IDs missing.", "danger");
        }
        return;
    }

    removeButton.disabled = true;
    tagPill.style.opacity = '0.5';

    try {
        const response = await authFetch(`/api/decks/${deckId}/tags/${tagId}`, {
            method: 'DELETE'
        });

        if (!response) throw new Error("Authentication or network error.");

        if (response.ok) {
             tagPill.remove();
        } else {
             const errorData = await response.json().catch(() => ({}));
             throw new Error(errorData.error || `Failed to remove tag (${response.status})`);
        }

    } catch (error) {
         console.error("Error removing tag:", error);
         if (typeof showFlashMessage === 'function') {
              showFlashMessage(error.message || "Could not remove tag.", "danger");
         }
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
        if (!response) {
             throw new Error("Authentication or network error.");
        }
        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }

        const filteredDecks = await response.json();
        sortAndRenderDecks(filteredDecks || [], sortValue);

    } catch (error) {
        console.error("Error fetching or rendering decks:", error);
        if (typeof showFlashMessage === 'function') {
             showFlashMessage("Error loading decks. " + error.message, "danger");
        }
        if (decksContainer) {
            decksContainer.innerHTML = '<p class="text-red-500 col-span-full">Error loading decks.</p>';
        }
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
                      openQuickAddTagModal(deckId, 'deck');
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