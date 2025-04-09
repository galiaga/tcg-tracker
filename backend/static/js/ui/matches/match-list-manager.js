import { authFetch } from '../../auth/auth.js';
import { formatMatchResult } from '../../utils.js';
import { openQuickAddTagModal, closeQuickAddTagModal } from '../tag-utils.js';

function getSelectedMatchTagIds() {
    const optionsContainer = document.getElementById("match-tag-filter-options");
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

export async function handleRemoveMatchTagClick(event) {
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
        if(typeof showFlashMessage === 'function') showFlashMessage("Could not remove tag: IDs missing.", "danger");
        return;
    }
    removeButton.disabled = true;
    tagPill.style.opacity = '0.5';
    try {
        const response = await authFetch(`/api/matches/${matchId}/tags/${tagId}`, { method: 'DELETE' });
        if (!response) throw new Error("Authentication or network error.");
        if (response.ok) {
            tagPill.remove();
        } else {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || `Failed to remove tag (${response.status})`);
        }
    } catch (error) {
        console.error("Error removing match tag:", error);
        if (typeof showFlashMessage === 'function') showFlashMessage(error.message || "Could not remove tag.", "danger");
        if (document.body.contains(removeButton)) {
             removeButton.disabled = false;
        }
         if (document.body.contains(tagPill)){
            tagPill.style.opacity = '1';
         }
    }
}

function displayMatches(matches, containerElement, noMatchesElement) {
    if (!containerElement) {
        console.error("Container element not provided for displayMatches.");
        return;
    }

    containerElement.innerHTML = "";
    if(noMatchesElement) {
        noMatchesElement.classList.add('hidden');
    }

    if (!matches || !Array.isArray(matches) || matches.length === 0) {
        if(noMatchesElement) {
            noMatchesElement.textContent = "No matches found matching the criteria.";
            noMatchesElement.classList.remove('hidden');
        } else {
            containerElement.innerHTML = `
                <div class="text-center text-violet-800 mt-4 p-4 text-base border border-dashed border-violet-300 rounded-lg md:col-span-2 xl:col-span-3">
                    No matches found.
                </div>
            `;
        }
        return;
    }

    const fragment = document.createDocumentFragment();
    const locale = navigator.language || 'en-US';
    const dateOptions = { dateStyle: 'medium', timeStyle: 'short' };

    matches.forEach(match => {
        const card = document.createElement("div");
        card.className = `relative bg-white shadow-md rounded-xl border border-gray-200 p-4 hover:shadow-lg transition-shadow duration-200 overflow-hidden`;
        card.dataset.matchId = match.id;

        const resultText = formatMatchResult(match.result);
        const lowerResult = resultText.toLowerCase();
        let badgeBgColorClass = 'bg-gray-400'; let badgeTextColorClass = 'text-gray-800';
        if (lowerResult === 'win') { badgeBgColorClass = 'bg-green-500'; badgeTextColorClass = 'text-white'; }
        else if (lowerResult === 'loss') { badgeBgColorClass = 'bg-red-500'; badgeTextColorClass = 'text-white'; }
        else if (lowerResult === 'draw') { badgeBgColorClass = 'bg-yellow-400'; badgeTextColorClass = 'text-gray-800'; }

        let formattedDate = 'N/A';
         if (match.date) { try { formattedDate = new Date(match.date).toLocaleString(locale, dateOptions); } catch(e) { formattedDate = match.date; } }

         const deckName = match.deck?.name ?? 'N/A';
         const deckTypeName = match.deck_type?.name ?? 'N/A';

         let tagPillsHtml = '';
         if (match.tags && match.tags.length > 0) {
             tagPillsHtml = match.tags.map(tag =>
                 `<span class="tag-pill inline-flex items-center gap-1 bg-violet-100 text-violet-800 text-xs font-medium px-2 py-0.5 rounded-md mr-1 mb-1" data-tag-id="${tag.id}">
                     ${tag.name}
                     <button type="button" class="remove-match-tag-button ml-0.5 text-violet-500 hover:text-violet-700 font-bold focus:outline-none" aria-label="Remove tag ${tag.name}">&times;</button>
                 </span>`
             ).join('');
         }
         const addTagButtonHtml = `<button type="button" class="add-match-tag-button inline-flex items-center text-xs font-medium px-2 py-0.5 rounded border border-dashed border-gray-400 text-gray-500 hover:bg-gray-100 hover:text-gray-700 hover:border-solid mb-1" aria-label="Add tag to match ${match.id}" data-match-id="${match.id}">+ Tag</button>`;
         const tagsContainerHtml = `<div class="mt-2 flex flex-wrap items-center gap-x-1">${tagPillsHtml}${addTagButtonHtml}</div>`;

         card.innerHTML = `<div class="flex items-start justify-between gap-3"><div class="flex-grow min-w-0"><h3 class="text-lg font-bold text-gray-800 break-words leading-tight truncate overflow-hidden">${deckName}</h3><p class="text-xs text-gray-500 mt-1">${formattedDate}</p></div><div class="flex flex-col items-end flex-shrink-0 space-y-1"><span class="text-xs ${badgeTextColorClass} ${badgeBgColorClass} px-2 py-0.5 rounded-full font-medium">${resultText}</span><span class="text-xs bg-violet-500 text-white px-2 py-0.5 rounded-full font-medium">${deckTypeName}</span></div></div>${tagsContainerHtml}`;
         fragment.appendChild(card);
     });
     containerElement.appendChild(fragment);
}

async function updateMatchHistoryView() {
    const matchesListContainer = document.getElementById("matches-list-items");
    const noMatchesMessage = document.getElementById("no-matches-message-history");

    if (!matchesListContainer || !noMatchesMessage) {
        console.error("Required UI elements for match history not found.");
        return;
    }

    matchesListContainer.innerHTML = '<div class="p-6 text-center text-gray-500">Loading match history...</div>';
    noMatchesMessage.classList.add('hidden');

    const selectedTagIds = getSelectedMatchTagIds();
    const params = new URLSearchParams();
    if (selectedTagIds.length > 0) {
        params.append('tags', selectedTagIds.join(','));
    }
    const apiUrl = `/api/matches_history?${params.toString()}`;

    try {
        const response = await authFetch(apiUrl);
        if (!response) throw new Error("Authentication or network error.");
         if (!response.ok) {
             let errorMsg = `Error loading match history: ${response.status}`;
             try { const errorData = await response.json(); errorMsg = errorData.error || errorMsg; } catch(e) {}
             throw new Error(errorMsg);
         }
        const userMatches = await response.json();
        if (!Array.isArray(userMatches)) throw new Error("Received invalid data format from server.");

        displayMatches(userMatches, matchesListContainer, noMatchesMessage);

    } catch (error) {
        console.error("Failed to fetch or process match history:", error);
        if (typeof showFlashMessage === 'function') showFlashMessage(error.message || "An unexpected error occurred loading history.", "danger");

        displayMatches([], matchesListContainer, noMatchesMessage);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const matchesContainer = document.getElementById('matches-list-items');
    if (!matchesContainer) {
        return;
    }

    const noMatchesMessage = document.getElementById("no-matches-message-history");

    const quickAddModal = document.getElementById("quickAddTagModal");
    const quickAddModalCloseBtn = document.getElementById("quickAddTagModalCloseButton");

    let initializedSomething = false;

    if (matchesContainer && noMatchesMessage) {
        updateMatchHistoryView();
        initializedSomething = true;

        matchesContainer.addEventListener('click', (event) => {
            if (event.target.closest('.remove-match-tag-button')) {
                handleRemoveMatchTagClick(event);
            } else if (event.target.closest('.add-match-tag-button')) {
                const addButton = event.target.closest('.add-match-tag-button');
                event.preventDefault();
                event.stopPropagation();
                const matchId = addButton.dataset.matchId;
                if (matchId && typeof openQuickAddTagModal === 'function') {
                    openQuickAddTagModal(matchId, 'match', updateMatchHistoryView);
                } else if (!matchId) {
                    console.error("Add tag button clicked on match, but no matchId found.");
                } else {
                    console.error("openQuickAddTagModal function not available.");
                }
            }
        });

        if (quickAddModal && quickAddModalCloseBtn && typeof closeQuickAddTagModal === 'function') {
            quickAddModalCloseBtn.addEventListener('click', closeQuickAddTagModal);
            quickAddModal.addEventListener('click', (event) => {
                if (event.target === quickAddModal) {
                    closeQuickAddTagModal();
                }
            });
        }
         initializedSomething = true;

    } else {
    }

    if (initializedSomething) {
     }

});

export { updateMatchHistoryView, displayMatches };