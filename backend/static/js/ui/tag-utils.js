import { authFetch } from '../auth/auth.js';
import { TagInputManager } from './tagInput.js';

let cachedUserTags = null;
let isFetchingTags = false;
let quickAddTagInputInstance = null;
let currentItemTypeForTagging = null;
let currentItemIdForTagging = null;
let currentRefreshCallback = null;

async function fetchUserTags(forceRefresh = false) {
    console.log(`[tag-utils] fetchUserTags called. forceRefresh=${forceRefresh}, cachedUserTags is ${cachedUserTags === null ? 'null' : 'not null'}`);
    if (!forceRefresh && cachedUserTags !== null) {
        console.log("[tag-utils] Returning cached tags.");
        return cachedUserTags;
    }
    if (isFetchingTags) {
        console.log("[tag-utils] Fetch already in progress, returning potentially stale cache or null.");
        return cachedUserTags;
    }
    isFetchingTags = true;
    console.log("[tag-utils] Fetching fresh tags from API...");
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
        console.log("[tag-utils] Successfully fetched and sorted fresh tags:", tags);
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
    console.log("[tag-utils] Invalidating tag cache.");
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

      console.log(`[tag-utils] Associating tag ID ${tagId} ("${tagName}") with ${itemType} ${itemId}...`);
      try {
          const response = await authFetch(apiUrl, {
              method: 'POST',
              body: JSON.stringify({ tag_id: tagId })
          });
           if (!response) throw new Error("Auth/Network Error during tag association");
          if (response.ok || response.status === 201) {
                console.log(`[tag-utils] Tag association API call successful (Status: ${response.status}).`);
                const responseData = await response.json().catch(()=>({}));
                invalidateTagCache(); 
                if (typeof showFlashMessage === 'function') {
                    const flashMsg = responseData.message || (response.status === 201 ? `Tag "${tagName}" added.` : `Tag "${tagName}" was already associated.`);
                    showFlashMessage(flashMsg, 'success');
                }
                if (typeof currentRefreshCallback === 'function') {
                    console.log("[tag-utils] Calling refresh callback...");
                    await currentRefreshCallback();
                    console.log("[tag-utils] Refresh callback finished.");
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

    console.log(`[tag-utils] Opening Quick Add Tag modal for ${itemType} ${itemId}.`);

    if (typeof TagInputManager !== 'undefined' && typeof TagInputManager.init === 'function') {
        if (quickAddTagInputInstance && typeof quickAddTagInputInstance.destroy === 'function') {
             quickAddTagInputInstance.destroy();
        }
        quickAddTagInputInstance = TagInputManager.init({
            inputId: 'quick-add-tag-input',
            suggestionsId: 'quick-add-tags-suggestions',
            containerId: 'quick-add-tags-container',
            onTagAdded: (tagData) => {
                console.log("[tag-utils] TagInputManager 'onTagAdded' triggered with:", tagData);
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
    console.log("[tag-utils] Closing Quick Add Tag modal.");
    if (quickAddTagInputInstance && typeof quickAddTagInputInstance.destroy === 'function') {
        quickAddTagInputInstance.destroy();
    }
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

export { fetchUserTags, invalidateTagCache, openQuickAddTagModal, closeQuickAddTagModal };