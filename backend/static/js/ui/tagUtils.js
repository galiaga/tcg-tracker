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
        const response = await authFetch("/api/tags");
        if (!response) {
             throw new Error("Auth or network error fetching tags");
        }
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
         return null;
    } finally {
         isFetchingTags = false;
    }
}

function invalidateTagCache() {
     cachedUserTags = null;
     isFetchingTags = false;
}

async function associateTag(tagData) {
      if (!currentItemIdForTagging || !currentItemTypeForTagging || !tagData || typeof tagData.id === 'undefined') {
          console.error("Missing item ID, type, or tag data for association");
          return;
      }
      const tagId = tagData.id;
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
           if (!response) throw new Error("Auth/Network Error");

          if (response.ok) {
               if (typeof showFlashMessage === 'function') {
                   showFlashMessage(`Tag "${tagData.name}" added to ${itemType} ${itemId}.`, 'success', 2000);
               }
               closeQuickAddTagModal();
               if (typeof currentRefreshCallback === 'function') {
                    currentRefreshCallback();
               }
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

function openQuickAddTagModal(itemId, itemType, refreshCallback) {
    const modal = document.getElementById("quickAddTagModal");
    const modalContent = modal?.querySelector(".bg-white");
    const title = modal?.querySelector("#quickAddTagModalTitle");
    const tagInputElement = document.getElementById('quick-add-tag-input');

    if (!modal || !modalContent || !title || !tagInputElement) {
        console.error("Quick Add Tag Modal elements not found.");
        return;
    }

    currentItemIdForTagging = itemId;
    currentItemTypeForTagging = itemType;
    currentRefreshCallback = refreshCallback;

    title.textContent = `Add Tag to ${itemType} #${itemId}`;

    if (typeof TagInputManager !== 'undefined') {
        quickAddTagInputInstance = TagInputManager.init({
             inputId: 'quick-add-tag-input',
             suggestionsId: 'quick-add-tags-suggestions',
             containerId: 'quick-add-tags-container',
             onTagAdded: (tagData) => {
                 associateTag(tagData);
             }
        });
        if (quickAddTagInputInstance) {
             quickAddTagInputInstance.clearTags();
             setTimeout(() => tagInputElement.focus(), 50);
        }
    } else {
         console.error("TagInputManager is not defined. Cannot initialize quick add modal input.");
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
    currentItemTypeForTagging = null;
    currentRefreshCallback = null;

    modalContent.classList.remove("scale-100", "opacity-100");
    modalContent.classList.add("scale-95", "opacity-0");
    setTimeout(() => {
        modal.classList.add("hidden");
    }, 150);
}

export { fetchUserTags, invalidateTagCache, openQuickAddTagModal, closeQuickAddTagModal };