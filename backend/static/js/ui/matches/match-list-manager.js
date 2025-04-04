import { authFetch } from '../../auth/auth.js';
import { formatMatchResult } from '../../utils.js';
import { TagInputManager } from '../tagInput.js';

let quickAddTagInputInstance = null;
let currentItemIdForTagging = null;

function getSelectedMatchTagIds() {
    const optionsContainer = document.getElementById("match-tag-filter-options");
    const selectedIds = [];
    if (!optionsContainer) {
        return selectedIds;
    }
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
               if (itemType === 'deck' && typeof updateDeckListView === 'function') {
                   updateDeckListView();
               } else if (itemType === 'match' && typeof updateMatchHistoryView === 'function') {
                   updateMatchHistoryView();
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

function openQuickAddTagModal(itemId, itemType = 'match') {
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

async function handleRemoveMatchTagClick(event) {
    const removeButton = event.target.closest('.remove-match-tag-button');
    if (!removeButton) return;

    event.preventDefault();
    event.stopPropagation();

    const tagPill = removeButton.closest('.tag-pill');
    const cardElement = removeButton.closest('[data-match-id]');

    if (!tagPill || !cardElement) return;

    const tagId = tagPill.dataset.tagId;
    const matchId = cardElement.dataset.matchId;

    if (!tagId || !matchId) {
        console.error("Could not find tagId or matchId for removal");
        if (typeof showFlashMessage === 'function') {
            showFlashMessage("Could not remove tag: IDs missing.", "danger");
        }
        return;
    }

    removeButton.disabled = true;
    tagPill.style.opacity = '0.5';

    try {
        const response = await authFetch(`/api/matches/${matchId}/tags/${tagId}`, {
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
         console.error("Error removing match tag:", error);
         if (typeof showFlashMessage === 'function') {
              showFlashMessage(error.message || "Could not remove tag.", "danger");
         }
         removeButton.disabled = false;
         tagPill.style.opacity = '1';
    }
}

async function updateMatchHistoryView() {
    const matchesListContainer = document.getElementById("matches-list-items");
    const noMatchesMessage = document.getElementById("no-matches-message-history");

    if (!matchesListContainer || !noMatchesMessage) {
        console.error("Required UI elements for match history rendering not found.");
        return;
    }

    const selectedTagIds = getSelectedMatchTagIds(); 

    const params = new URLSearchParams();
    if (selectedTagIds.length > 0) {
        params.append('tags', selectedTagIds.join(','));
    }

    const apiUrl = `/api/matches_history?${params.toString()}`;
    matchesListContainer.innerHTML = '<div class="p-6 text-center text-gray-500">Loading match history...</div>';
    noMatchesMessage.classList.add('hidden');

    try {
        const response = await authFetch(apiUrl);

        if (!response) {
            throw new Error("Authentication or network error.");
        }
         if (!response.ok) {
             let errorMsg = `Error loading match history: ${response.status}`;
             try { const errorData = await response.json(); errorMsg = errorData.error || errorMsg; } catch(e) {}
             throw new Error(errorMsg);
         }

        const userMatches = await response.json();

        if (!Array.isArray(userMatches)) {
             throw new Error("Received invalid data format from server.");
        }

        matchesListContainer.innerHTML = "";

        if (userMatches.length === 0) {
            noMatchesMessage.textContent = "No match history found for the selected filters.";
            noMatchesMessage.classList.remove('hidden');
            return;
        }

        noMatchesMessage.classList.add('hidden');

        const fragment = document.createDocumentFragment();
        const locale = navigator.language || 'en-US';
        const dateOptions = { dateStyle: 'medium', timeStyle: 'short' };

        userMatches.forEach(match => {
            const card = document.createElement("div");
            card.className = `relative bg-white shadow-md rounded-xl border border-gray-200 p-4 hover:shadow-lg transition-shadow duration-200`;
            card.dataset.matchId = match.id;

            const resultText = formatMatchResult(match.result);
            const lowerResult = resultText.toLowerCase();

            let badgeBgColorClass = 'bg-gray-400';
            let badgeTextColorClass = 'text-gray-800';

            if (lowerResult === 'win') {
                badgeBgColorClass = 'bg-green-500';
                badgeTextColorClass = 'text-white';
            } else if (lowerResult === 'loss') {
                badgeBgColorClass = 'bg-red-500';
                 badgeTextColorClass = 'text-white';
            } else if (lowerResult === 'draw') {
                badgeBgColorClass = 'bg-yellow-400';
                 badgeTextColorClass = 'text-gray-800';
            }

            let formattedDate = 'N/A';
             if (match.date) {
                 try {
                     formattedDate = new Date(match.date).toLocaleString(locale, dateOptions);
                 } catch(e) {
                     console.warn(`Could not format date: ${match.date}`, e);
                     formattedDate = match.date;
                 }
             }

             const deckName = match.deck?.name ?? 'N/A';
             const deckTypeName = match.deck_type?.name ?? 'N/A';

             let tagPillsHtml = '';
             if (match.tags && match.tags.length > 0) {
                 tagPillsHtml = match.tags.map(tag =>
                     `<span class="tag-pill inline-flex items-center gap-1 bg-gray-200 text-gray-700 text-xs font-medium px-2 py-0.5 rounded-full mr-1 mb-1" data-tag-id="${tag.id}">
                         ${tag.name}
                         <button type="button" class="remove-match-tag-button ml-0.5 text-gray-400 hover:text-gray-600 font-bold focus:outline-none" aria-label="Remove tag ${tag.name}">&times;</button>
                     </span>`
                 ).join('');
             }

             const addTagButtonHtml = `
                 <button type="button" class="add-match-tag-button inline-flex items-center text-xs font-medium px-2 py-0.5 rounded border border-dashed border-gray-400 text-gray-500 hover:bg-gray-100 hover:text-gray-700 hover:border-solid mb-1" aria-label="Add tag to match ${match.id}" data-match-id="${match.id}">
                     + Tag
                 </button>
             `;

             const tagsContainerHtml = `<div class="mt-2 flex flex-wrap items-center gap-x-1">${tagPillsHtml}${addTagButtonHtml}</div>`;

             card.innerHTML = `
                <div class="flex items-start justify-between gap-3">
                    <div class="flex-grow min-w-0">
                        <h3 class="text-lg font-bold text-gray-800 break-words leading-tight truncate">${deckName}</h3>
                        <p class="text-xs text-gray-500 mt-1">${formattedDate}</p>
                    </div>
                    <div class="flex flex-col items-end flex-shrink-0 space-y-1">
                        <span class="text-xs ${badgeTextColorClass} ${badgeBgColorClass} px-2 py-0.5 rounded-full font-medium whitespace-nowrap">
                            ${resultText}
                        </span>
                        <span class="text-xs bg-blue-500 text-white px-2 py-0.5 rounded-full font-medium whitespace-nowrap">
                            ${deckTypeName}
                        </span>
                    </div>
                </div>
                ${tagsContainerHtml}
            `;

            fragment.appendChild(card);
        });

        matchesListContainer.appendChild(fragment);

    } catch (error) {
        if (typeof showFlashMessage === 'function') {
             showFlashMessage(error.message || "An unexpected error occurred loading history.", "danger");
        }
        matchesListContainer.innerHTML = "";
        noMatchesMessage.textContent = "Could not load match history due to an error.";
        noMatchesMessage.classList.remove('hidden');
    }
}

export { updateMatchHistoryView };

document.addEventListener('DOMContentLoaded', () => {
    const matchesContainer = document.getElementById('matches-list-items');
    const tagFilterButton = document.getElementById("match-tag-filter-button");
    const tagFilterDropdown = document.getElementById("match-tag-filter-dropdown");
    const quickAddModal = document.getElementById("quickAddTagModal");
    const quickAddModalCloseBtn = document.getElementById("quickAddTagModalCloseButton");

    if (matchesContainer && tagFilterButton && tagFilterDropdown && quickAddModal && quickAddModalCloseBtn)
    {
        updateMatchHistoryView();

        matchesContainer.addEventListener('click', (event) => {
            if (event.target.closest('.remove-match-tag-button')) {
                 handleRemoveMatchTagClick(event);
            } else if (event.target.closest('.add-match-tag-button')) {
                 const addButton = event.target.closest('.add-match-tag-button');
                 event.preventDefault();
                 event.stopPropagation();
                 const matchId = addButton.dataset.matchId;
                 if (matchId) {
                      openQuickAddTagModal(matchId, 'match');
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
         console.warn("Match list manager could not initialize fully - required elements missing (incl. quick add modal or filters).");
    }
});