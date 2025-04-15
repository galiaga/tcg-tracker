import { authFetch } from '../auth/auth.js';
import { TagInputManager } from './tagInput.js';

let cachedUserTags = null;
let isFetchingTags = false;
let quickAddTagInputInstance = null;
let currentItemTypeForTagging = null;
let currentItemIdForTagging = null;
let currentRefreshCallback = null;

async function fetchUserTags(forceRefresh = false) {
    if (!forceRefresh && cachedUserTags !== null) {
        return cachedUserTags;
    }
    if (isFetchingTags) {
        return cachedUserTags;
    }
    isFetchingTags = true;
    try {
        const response = await authFetch("/api/tags", {
             headers: {
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0'
            }
        });
        if (!response) { throw new Error("Auth or network error fetching tags"); }
        if (!response.ok) {
            console.error("tagUtils.js: API response not OK", response);
            throw new Error(`Failed to fetch tags: ${response.status}`);
        }
        const tags = await response.json();
        tags.sort((a, b) => a.name.localeCompare(b.name));
        cachedUserTags = tags;
        return tags;
    } catch (error) {
         console.error("Error in fetchUserTags utility:", error);
         cachedUserTags = null;
         return null;
    } finally {
         isFetchingTags = false;
    }
}

function invalidateTagCache() {
    cachedUserTags = null;
}

async function associateTag(tagData) {
      if (!currentItemIdForTagging || !currentItemTypeForTagging || !tagData || typeof tagData.id === 'undefined') {
          console.error("Missing item ID, type, or tag data for association");
          return;
      }
      const tagId = tagData.id;
      const tagName = tagData.name;
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
          if (response.ok || response.status === 201) {
                const responseData = await response.json().catch(()=>({}));
                invalidateTagCache(); 
                if (typeof showFlashMessage === 'function') {
                    const flashMsg = responseData.message || (response.status === 201 ? `Tag "${tagName}" added.` : `Tag "${tagName}" was already associated.`);
                    showFlashMessage(flashMsg, 'success');
                }
                if (typeof currentRefreshCallback === 'function') {
                    await currentRefreshCallback();
                } else {
                    console.warn("[tag-utils] No refresh callback provided or it's not a function.");
                }
                closeQuickAddTagModal();
          } else {
                const errorData = await response.json().catch(() => ({}));
                console.error(`[tag-utils] Failed to associate tag. Status: ${response.status}`, errorData);
                throw new Error(errorData.error || `Failed to add tag (${response.status})`);
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
             return true;
        } else {
             const errorData = await response.json().catch(() => ({}));
             console.error(`[tag-utils] API error removing tag ${tagId} from deck ${deckId}. Status: ${response.status}`, errorData);
             throw new Error(errorData.error || `Failed to remove tag (${response.status})`);
        }
    } catch (error) {
        console.error(`[tag-utils] Error in handleRemoveDeckTagClick for tag ${tagId}, deck ${deckId}:`, error);
        if (typeof showFlashMessage === 'function') showFlashMessage(error.message || "Could not remove tag.", "danger");
        removeButton.disabled = false;
        tagPill.style.opacity = '1';
        return false;
    }
}

function openQuickAddTagModal(itemId, itemType, refreshCallback) {

    const modal = document.getElementById("quickAddTagModal");
    const modalContent = modal?.querySelector(".bg-white"); 
    const title = modal?.querySelector("#quickAddTagModalTitle");
    const tagInputElement = document.getElementById('quick-add-tag-input');

    if (!modal || !modalContent || !title || !tagInputElement) {
        console.error("Quick Add Tag Modal elements not found. Cannot open modal.");
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
            containerId: 'quick-add-tags-container',
            onTagAdded: (tagData) => {
                associateTag(tagData); 
            },
            fetchSuggestions: async (query) => {
                const tags = await fetchUserTags(); 
                if (!tags) return [];
                return tags.filter(tag => tag.name.toLowerCase().includes(query.toLowerCase()));
            },
        });

        if (quickAddTagInputInstance) {
             quickAddTagInputInstance.clearTags(); 
             setTimeout(() => tagInputElement.focus(), 50);
        } else {
              console.error("[tag-utils] Failed to initialize TagInputManager instance.");
        }
    } else {
         console.error("[tag-utils] TagInputManager is not defined or init is not a function.");
    }

    modal.classList.remove("hidden");
    setTimeout(() => {
      if (modalContent) {
          modalContent.classList.remove("scale-95", "opacity-0");
          modalContent.classList.add("scale-100", "opacity-100");
      }
    }, 10); 
}

function closeQuickAddTagModal() {
    const modal = document.getElementById("quickAddTagModal");
    const modalContent = modal?.querySelector(".bg-white");
    
    if (!modal || !modalContent) return;

    quickAddTagInputInstance = null;
    currentItemIdForTagging = null;
    currentItemTypeForTagging = null;
    currentRefreshCallback = null;
    modalContent.classList.remove("scale-100", "opacity-100");
    modalContent.classList.add("scale-95", "opacity-0");
    setTimeout(() => {
        modal.classList.add("hidden");
    }, 150);
}

export { fetchUserTags, invalidateTagCache, openQuickAddTagModal, closeQuickAddTagModal, handleRemoveTagClick };