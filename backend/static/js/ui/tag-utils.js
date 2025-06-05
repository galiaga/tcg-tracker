import { authFetch } from '../auth/auth.js';
import { TagInputManager } from './tagInput.js'; 

let quickAddTagInputInstance = null;
let currentItemTypeForTagging = null;
let currentItemIdForTagging = null;
let currentRefreshCallback = null;

// Define the function WITHOUT 'export' keyword here
function openQuickAddTagModal(itemId, itemType, refreshCallback) { // Removed 'export'
    console.log("[tag-utils.js] openQuickAddTagModal called with:", { itemId, itemType });

    const modal = document.getElementById("quickAddTagModal");
    const title = document.getElementById("quickAddTagModalTitle"); 
    const tagInputElement = document.getElementById('quick-add-tag-input');
    const suggestionsElement = document.getElementById('quick-add-tags-suggestions'); 
    const closeButton = document.getElementById("quickAddTagModalCloseButton");
    const doneButton = document.getElementById("quickAddTagModalDoneButton");

    console.log("[tag-utils.js] Modal element:", modal);
    console.log("[tag-utils.js] Title element:", title);
    console.log("[tag-utils.js] Tag input element:", tagInputElement);
    console.log("[tag-utils.js] Suggestions element:", suggestionsElement);
    console.log("[tag-utils.js] Close button:", closeButton);
    console.log("[tag-utils.js] Done button:", doneButton);

    if (!modal || !title || !tagInputElement || !suggestionsElement || !closeButton || !doneButton) {
        console.error("[tag-utils.js] CRITICAL: Quick Add Tag Modal or one of its core elements not found in the DOM.");
        if (typeof showFlashMessage === 'function') {
            showFlashMessage("Error: Tagging UI components are missing. Please refresh.", "danger");
        }
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
            },
            isCommanderSearch: false 
        });

        if (quickAddTagInputInstance && typeof quickAddTagInputInstance.clearInput === 'function') {
             quickAddTagInputInstance.clearInput();
             setTimeout(() => tagInputElement.focus(), 50);
        } else if (!quickAddTagInputInstance) {
              console.error("[tag-utils.js] Failed to initialize TagInputManager for Quick Add Modal.");
        }
    } else {
         console.error("[tag-utils.js] TagInputManager is not defined or init is not a function.");
    }

    const localCloseHandler = () => closeQuickAddTagModal();
    const localDoneHandler = () => closeQuickAddTagModal(); 
    const localOverlayClickHandler = (event) => { if (event.target === modal) closeQuickAddTagModal(); };
    
    // Store handlers on elements to ensure correct removal if elements persist but listeners change
    if(closeButton) { // Check if element exists before adding listener
        closeButton._clickHandler = localCloseHandler; 
        closeButton.addEventListener('click', localCloseHandler);
    }
    if(doneButton) {
        doneButton._clickHandler = localDoneHandler;
        doneButton.addEventListener('click', localDoneHandler);
    }
    if(modal) {
        modal._overlayClickHandler = localOverlayClickHandler;
        modal.addEventListener('click', localOverlayClickHandler);
    }

    modal.classList.remove("hidden");
    const modalContent = modal.querySelector(".bg-white, .dark\\:bg-gray-800");
    if (modalContent) {
        setTimeout(() => {
            modalContent.classList.remove("scale-95", "opacity-0");
            modalContent.classList.add("scale-100", "opacity-100");
        }, 10);
    }
}

// Define the function WITHOUT 'export' keyword here
function closeQuickAddTagModal() { // Removed 'export'
    const modal = document.getElementById("quickAddTagModal"); 
    if (!modal) return;

    const closeButton = document.getElementById("quickAddTagModalCloseButton");
    const doneButton = document.getElementById("quickAddTagModalDoneButton");

    if (closeButton && closeButton._clickHandler) {
        closeButton.removeEventListener('click', closeButton._clickHandler);
        delete closeButton._clickHandler;
    }
    if (doneButton && doneButton._clickHandler) {
        doneButton.removeEventListener('click', doneButton._clickHandler);
        delete doneButton._clickHandler;
    }
    if (modal._overlayClickHandler) {
        modal.removeEventListener('click', modal._overlayClickHandler);
        delete modal._overlayClickHandler;
    }

    if (quickAddTagInputInstance && typeof quickAddTagInputInstance.destroy === 'function') {
        quickAddTagInputInstance.destroy();
    }
    quickAddTagInputInstance = null;
    currentItemIdForTagging = null;
    currentItemTypeForTagging = null;
    currentRefreshCallback = null;

    const modalContent = modal.querySelector(".bg-white, .dark\\:bg-gray-800");
    if (modalContent) {
        modalContent.classList.remove("scale-100", "opacity-100");
        modalContent.classList.add("scale-95", "opacity-0");
    }
    setTimeout(() => {
        modal.classList.add("hidden");
    }, 150);
}

// Define the function WITHOUT 'export' keyword here
async function associateTag(tagData) { // Removed 'export'
      if (!currentItemIdForTagging || !currentItemTypeForTagging || !tagData || typeof tagData.id === 'undefined') {
          console.error("Missing item ID, type, or tag data for association");
          if (typeof showFlashMessage === 'function') showFlashMessage("Error: Could not associate tag. Missing data.", "danger");
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
          
           const responseData = await response.json().catch(()=>({}));

          if (response.ok || response.status === 201) {
                if (typeof showFlashMessage === 'function') {
                    const flashMsg = responseData.message || (response.status === 201 ? `Tag "${tagName}" added.` : `Tag "${tagName}" associated.`);
                    showFlashMessage(flashMsg, 'success');
                }
                if (typeof currentRefreshCallback === 'function') {
                    await currentRefreshCallback();
                }
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

// Define the function WITHOUT 'export' keyword here
async function handleRemoveDeckTagClick(deckId, tagId, refreshCallback, clickedButtonElement, tagPillElement) { // Removed 'export'
    if (!tagId || !deckId) {
        console.error("Could not find tagId or deckId for removal");
        if (typeof showFlashMessage === 'function') showFlashMessage("Could not remove tag: IDs missing.", "danger");
        return false;
    }

    if (clickedButtonElement) clickedButtonElement.disabled = true;
    if (tagPillElement) tagPillElement.style.opacity = '0.5';

    const apiUrl = `/api/decks/${deckId}/tags/${tagId}`;

    try {
        const response = await authFetch(apiUrl, { method: 'DELETE' });
        if (!response) throw new Error("Authentication or network error.");
        
        let responseData = {};
        if (response.status !== 204) { 
            responseData = await response.json().catch(() => ({}));
        }

        if (response.ok) {
             if (typeof showFlashMessage === 'function') {
                 showFlashMessage(responseData.message || "Tag removed successfully.", "success");
             }
             if (typeof refreshCallback === 'function') {
                await refreshCallback();
             }
             return true;
        } else {
             console.error(`[tag-utils] API error removing tag. Status: ${response.status}`, responseData);
             throw new Error(responseData.error || `Failed to remove tag (${response.status})`);
        }
    } catch (error) {
        console.error(`[tag-utils] Error in handleRemoveDeckTagClick:`, error);
        if (typeof showFlashMessage === 'function') showFlashMessage(error.message || "Could not remove tag.", "danger");
        if (clickedButtonElement && document.body.contains(clickedButtonElement)) clickedButtonElement.disabled = false;
        if (tagPillElement && document.body.contains(tagPillElement)) tagPillElement.style.opacity = '1';
        return false;
    }
}

const fetchAllUserTags = TagInputManager.fetchAllUserTags; 

// NOW, explicitly export all the functions you need externally
export { 
    fetchAllUserTags, 
    openQuickAddTagModal, 
    closeQuickAddTagModal, 
    handleRemoveDeckTagClick,
    associateTag // Export associateTag if it's called from elsewhere, or keep it internal
};