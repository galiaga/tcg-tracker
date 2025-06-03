// backend/static/js/ui/tag-utils.js
import { authFetch } from '../auth/auth.js';
import { TagInputManager } from './tagInput.js'; // Using the older version

let quickAddTagInputInstance = null; // Instance for the modal's tag input
let currentItemTypeForTagging = null;
let currentItemIdForTagging = null;
let currentRefreshCallback = null;

// fetchUserTags and invalidateTagCache are NOT imported or used here
// as the older TagInputManager handles its own global cache.

async function associateTag(tagData) { // tagData is {id, name}
      if (!currentItemIdForTagging || !currentItemTypeForTagging || !tagData || typeof tagData.id === 'undefined') {
          console.error("Missing item ID, type, or tag data for association");
          if (typeof showFlashMessage === 'function') showFlashMessage("Error: Could not associate tag. Missing data.", "danger");
          return;
      }
      const tagId = tagData.id;
      const tagName = tagData.name; // For flash message
      const itemId = currentItemIdForTagging;
      const itemType = currentItemTypeForTagging;
      const apiUrl = itemType === 'deck'
                      ? `/api/decks/${itemId}/tags`
                      : `/api/matches/${itemId}/tags`;

      try {
          const response = await authFetch(apiUrl, {
              method: 'POST',
              body: JSON.stringify({ tag_id: tagId })
          });
           if (!response) throw new Error("Auth/Network Error during tag association");
          
           const responseData = await response.json().catch(()=>({}));

          if (response.ok || response.status === 201) {
                // TagInputManager's global cache will be updated by its own logic if a new tag was created.
                if (typeof showFlashMessage === 'function') {
                    const flashMsg = responseData.message || (response.status === 201 ? `Tag "${tagName}" added.` : `Tag "${tagName}" associated.`);
                    showFlashMessage(flashMsg, 'success');
                }
                if (typeof currentRefreshCallback === 'function') {
                    await currentRefreshCallback();
                }
                // With the older TagInputManager, onTagAdded triggers this, and then we close the modal.
                closeQuickAddTagModal(); 
          } else {
                console.error(`[tag-utils] Failed to associate tag. Status: ${response.status}`, responseData);
                throw new Error(responseData.error || `Failed to add tag (${response.status})`);
          }
      } catch (error) {
           console.error(`[tag-utils] Error associating tag ${tagId} with ${itemType} ${itemId}:`, error);
           if (typeof showFlashMessage === 'function') {
                showFlashMessage(error.message || `Could not add tag.`, 'danger');
           }
      }
}

async function handleRemoveTagClick(event) {
    const removeButton = event.target.closest('.remove-tag-button');
    if (!removeButton) return false;

    event.preventDefault();
    event.stopPropagation();

    const tagPill = removeButton.closest('.tag-pill');
    const cardElement = removeButton.closest('[data-deck-id]'); 

    if (!tagPill || !cardElement) {
        console.error("Could not find tagPill or cardElement for tag removal.");
        if (typeof showFlashMessage === 'function') showFlashMessage("Error: Could not identify tag or item for removal.", "danger");
        return false;
    }

    const tagId = tagPill.dataset.tagId;
    const itemId = cardElement.dataset.deckId; 
    const itemType = 'deck'; 

    if (!tagId || !itemId) {
        console.error("Could not find tagId or itemId for removal");
        if (typeof showFlashMessage === 'function') showFlashMessage("Could not remove tag: IDs missing.", "danger");
        return false;
    }

    removeButton.disabled = true;
    tagPill.style.opacity = '0.5';

    const apiUrl = `/api/decks/${itemId}/tags/${tagId}`;

    try {
        const response = await authFetch(apiUrl, { method: 'DELETE' });
        if (!response) throw new Error("Authentication or network error.");
        
        const responseData = await response.json().catch(() => ({}));

        if (response.ok) {
             tagPill.remove();
             if (typeof showFlashMessage === 'function') {
                 showFlashMessage(responseData.message || "Tag removed successfully.", "success");
             }
             // The TagInputManager's global cache is not directly affected by removing a tag from a deck,
             // so no explicit cache invalidation for TagInputManager is needed here.
             return true;
        } else {
             console.error(`[tag-utils] API error removing tag. Status: ${response.status}`, responseData);
             throw new Error(responseData.error || `Failed to remove tag (${response.status})`);
        }
    } catch (error) {
        console.error(`[tag-utils] Error in handleRemoveTagClick:`, error);
        if (typeof showFlashMessage === 'function') showFlashMessage(error.message || "Could not remove tag.", "danger");
        removeButton.disabled = false;
        tagPill.style.opacity = '1';
        return false;
    }
}

function openQuickAddTagModal(itemId, itemType, refreshCallback) {
    const modal = document.getElementById("quickAddTagModal");
    const modalContent = modal?.querySelector(".bg-white, .dark\\:bg-gray-800");
    const title = modal?.querySelector("#quickAddTagModalTitle");
    const tagInputElement = document.getElementById('quick-add-tag-input');

    if (!modal || !title || !tagInputElement) {
        console.error("Quick Add Tag Modal or its core input elements not found.");
        if (typeof showFlashMessage === 'function') showFlashMessage("Error: UI for adding tags is missing.", "danger");
        return; 
    }

    currentItemIdForTagging = itemId;
    currentItemTypeForTagging = itemType;
    currentRefreshCallback = refreshCallback; 

    title.textContent = `Add Tag to ${itemType === 'deck' ? 'Deck' : 'Match'}`; 

    if (typeof TagInputManager !== 'undefined' && typeof TagInputManager.init === 'function') {
        if (quickAddTagInputInstance && typeof quickAddTagInputInstance.destroy === 'function') {
             quickAddTagInputInstance.destroy();
        }
        
        quickAddTagInputInstance = TagInputManager.init({
            inputId: 'quick-add-tag-input',
            suggestionsId: 'quick-add-tags-suggestions',
            onTagAdded: (tagData) => {
                associateTag(tagData); 
            }
            // No fetchSuggestions needed here for the older TagInputManager
        });

        if (quickAddTagInputInstance && typeof quickAddTagInputInstance.clearInput === 'function') {
             quickAddTagInputInstance.clearInput();
             setTimeout(() => {
                if (tagInputElement) tagInputElement.focus();
            }, 50);
        } else if (!quickAddTagInputInstance) {
              console.error("[tag-utils] Failed to initialize TagInputManager instance for Quick Add Modal.");
              if (typeof showFlashMessage === 'function') showFlashMessage("Error: Could not initialize tag input.", "danger");
        }
    } else {
         console.error("[tag-utils] TagInputManager is not defined or init is not a function.");
         if (typeof showFlashMessage === 'function') showFlashMessage("Error: Tag management script not loaded.", "danger");
    }

    modal.classList.remove("hidden");
    if (modalContent) {
        setTimeout(() => {
            modalContent.classList.remove("scale-95", "opacity-0");
            modalContent.classList.add("scale-100", "opacity-100");
        }, 10);
    }
}

function closeQuickAddTagModal() {
    const modal = document.getElementById("quickAddTagModal");
    const modalContent = modal?.querySelector(".bg-white, .dark\\:bg-gray-800");
    
    if (!modal) return;

    if (quickAddTagInputInstance && typeof quickAddTagInputInstance.destroy === 'function') {
        quickAddTagInputInstance.destroy();
    }
    quickAddTagInputInstance = null;

    currentItemIdForTagging = null;
    currentItemTypeForTagging = null;
    currentRefreshCallback = null;

    if (modalContent) {
        modalContent.classList.remove("scale-100", "opacity-100");
        modalContent.classList.add("scale-95", "opacity-0");
    }
    setTimeout(() => {
        modal.classList.add("hidden");
    }, 150);
}

// Export fetchAllUserTags from TagInputManager if other modules need to preload tags.
// If not, this export can also be removed.
const fetchAllUserTags = TagInputManager.fetchAllUserTags; 
export { fetchAllUserTags, openQuickAddTagModal, closeQuickAddTagModal, handleRemoveTagClick };