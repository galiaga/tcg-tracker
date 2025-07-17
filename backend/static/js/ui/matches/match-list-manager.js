// backend/static/js/ui/matches/match-list-manager.js

import { authFetch } from '../../auth/auth.js';
import { formatMatchResult } from '../../utils.js';
import { openQuickAddTagModal, closeQuickAddTagModal } from '../tag-utils.js';
import { initializeMatchActionMenus } from './match-actions.js';

// --- Core Functions ---

function getSelectedMatchTagIds() {
    const optionsContainer = document.getElementById("match-tag-filter-options");
    if (!optionsContainer) return [];

    // Get all checked checkboxes
    const checkedCheckboxes = Array.from(optionsContainer.querySelectorAll('input[type="checkbox"]:checked'));

    return checkedCheckboxes
        .filter(checkbox => checkbox.id !== 'select-all-match-tags-checkbox')
        .map(checkbox => checkbox.value);
}

async function handleRemoveMatchTagClick(event) {
    const removeButton = event.target.closest('.remove-match-tag-button');
    if (!removeButton) return false;

    event.preventDefault();
    event.stopPropagation();

    const tagPill = removeButton.closest('.tag-pill');
    const cardElement = removeButton.closest('.match-item');
    const tagId = tagPill?.dataset.tagId;
    const matchId = cardElement?.dataset.matchId;

    if (!tagId || !matchId) {
        console.warn("Missing tagId or matchId for removal.");
        return false;
    }

    removeButton.disabled = true;
    if (tagPill) tagPill.style.opacity = '0.5';

    try {
        const response = await authFetch(`/api/matches/${matchId}/tags/${tagId}`, {
            method: 'DELETE',
        });

        if (!response) throw new Error("Authentication or network error.");
        
        const responseData = await response.json().catch(() => ({}));

        if (response.ok) {
            if (tagPill) tagPill.remove();
            return true;
        } else {
            throw new Error(responseData.error || `Failed to remove tag (${response.status})`);
        }
    } catch (error) {
        console.error("Error removing match tag:", error);
        if (document.body.contains(removeButton)) removeButton.disabled = false;
        if (document.body.contains(tagPill)) tagPill.style.opacity = '1';
        return false;
    }
}

function displayMatches(matches, containerElement, noMatchesElement) {
    if (!containerElement) {
        console.error("Match display container not found.");
        return;
    }

    containerElement.innerHTML = ""; // Clear previous
    const hasMatches = matches && Array.isArray(matches) && matches.length > 0;

    if (noMatchesElement) {
        noMatchesElement.classList.toggle('hidden', hasMatches);
        if (!hasMatches) {
            noMatchesElement.className = "w-full text-center text-gray-500 dark:text-gray-400 mt-8 p-6 text-base border border-dashed border-gray-300 dark:border-gray-600 rounded-lg md:col-span-2";
            noMatchesElement.textContent = "No matches found matching the criteria.";
        }
    }

    if (!hasMatches) {
        if (!noMatchesElement) { 
            containerElement.innerHTML = `<div class="text-center text-violet-500 dark:text-violet-400 mt-4 p-6 text-base border border-dashed border-violet-300 dark:border-violet-600 rounded-lg md:col-span-2">No matches found.</div>`;
        }
        return;
    }

    const fragment = document.createDocumentFragment();
    const locale = navigator.language || 'en-US'; 
    const dateOptions = { month: 'short', day: 'numeric', year: 'numeric', hour: 'numeric', minute: '2-digit', hour12: true };

    const renderOpponentsHtml = (opponents) => {
        if (!opponents || opponents.length === 0) {
            return '';
        }

        const opponentPills = opponents.map(name => 
            `<li class="inline-block bg-slate-200 dark:bg-slate-700 text-slate-600 dark:text-slate-300 text-xs font-medium px-2.5 py-1 rounded-full">
                ${name}
            </li>`
        ).join('');

        return `
            <div class="flex items-start gap-3">
                <h4 class="flex-shrink-0 text-xs font-bold uppercase text-slate-400 dark:text-slate-500 pt-1">Opponents</h4>
                <ul class="flex flex-wrap gap-2">
                    ${opponentPills}
                </ul>
            </div>
        `;
    };

    matches.forEach(match => {
        const card = document.createElement("div");
        card.className = `match-item relative bg-white dark:bg-slate-800 shadow-lg rounded-lg p-4 flex flex-col space-y-3 border-l-4 hover:shadow-xl transition-shadow duration-200 ease-in-out`;
        card.dataset.matchId = match.id;

        const deckName = match.deck?.name ?? 'Unknown Deck';
        const escapedDeckName = deckName.replace(/"/g, '"');
        let formattedDate = 'N/A';
        if (match.date) {
            try { formattedDate = new Date(match.date).toLocaleString(locale, dateOptions); }
            catch (e) { formattedDate = match.date; }
        }
        const resultText = formatMatchResult(match.result); 
        const lowerResult = (resultText || "").toLowerCase();
        
        let resultBadgeClass = 'bg-gray-200 text-gray-800 dark:bg-gray-600 dark:text-gray-100';
        let borderColorClassString = 'border-gray-300 dark:border-gray-600';

        if (lowerResult === 'win') {
            resultBadgeClass = 'bg-green-100 text-green-700 dark:bg-green-700 dark:text-green-100';
            borderColorClassString = 'border-green-500 dark:border-green-500';
        } else if (lowerResult === 'loss') {
            resultBadgeClass = 'bg-red-100 text-red-700 dark:bg-red-700 dark:text-red-100';
            borderColorClassString = 'border-red-500 dark:border-red-500';
        }
        
        card.classList.add(...borderColorClassString.split(' ')); 

        const tagPillsHtml = (match.tags || []).map(tag => {
            const escapedTagName = tag.name.replace(/"/g, '"');
            return `<span class="tag-pill inline-flex items-center whitespace-nowrap bg-violet-100 dark:bg-violet-700/60 px-2.5 py-1 text-xs font-semibold text-violet-700 dark:text-violet-200 rounded-full" data-tag-id="${tag.id}">
                <span>${tag.name}</span>
                <button type="button" class="remove-match-tag-button ml-1.5 -mr-0.5 flex-shrink-0 rounded-full p-0.5 text-violet-500 dark:text-violet-400 hover:bg-violet-200 dark:hover:bg-violet-600 focus:outline-none focus:ring-1 focus:ring-violet-400 dark:focus:ring-violet-500" aria-label="Remove ${escapedTagName} from match">
                    <svg class="h-2.5 w-2.5" stroke="currentColor" fill="none" viewBox="0 0 8 8"><path stroke-linecap="round" stroke-width="1.5" d="M1 1l6 6m0-6L1 7" /></svg>
                </button>
            </span>`;
        }).join('');
        
        const addTagButtonHtml = `
            <button type="button" class="add-match-tag-button text-xs font-medium text-violet-600 dark:text-violet-400 hover:text-violet-800 dark:hover:text-violet-200 border border-dashed border-violet-400 dark:border-violet-500 rounded-full px-2.5 py-1 hover:bg-violet-100 dark:hover:bg-violet-700/30 transition-colors leading-tight focus:outline-none focus:ring-1 focus:ring-violet-500" aria-label="Add tag to match" data-match-id="${match.id}">
                + Tag
            </button>`;

        const opponentsHtml = renderOpponentsHtml(match.opponents);
        
        card.innerHTML = `
            <div class="flex justify-between items-center gap-4">
                <!-- Left Side: Deck Name and Date -->
                <div class="flex-grow min-w-0">
                    <h3 class="text-lg font-semibold text-gray-900 dark:text-white leading-tight truncate" title="${escapedDeckName}">${deckName}</h3>
                    <p class="text-xs text-gray-500 dark:text-gray-400">${formattedDate}</p>
                </div>

                <!-- Right Side: Result Pill and Options Menu -->
                <div class="flex-shrink-0 flex items-center gap-3">
                    <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold ${resultBadgeClass}">${resultText}</span>
                    <div class="relative match-actions">
                         <button type="button" class="match-options-btn p-1.5 rounded-full text-gray-400 dark:text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700 hover:text-gray-600 dark:hover:text-gray-300 focus:outline-none focus:ring-2 focus:ring-offset-1 dark:focus:ring-offset-slate-800 focus:ring-violet-500" data-match-id="${match.id}" aria-label="Match options" aria-haspopup="true" aria-expanded="false">
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5 pointer-events-none"><path stroke-linecap="round" stroke-linejoin="round" d="M12 6.75a.75.75 0 1 1 0-1.5.75.75 0 0 1 0 1.5ZM12 12.75a.75.75 0 1 1 0-1.5.75.75 0 0 1 0 1.5ZM12 18.75a.75.75 0 1 1 0-1.5.75.75 0 0 1 0 1.5Z" /></svg>
                        </button>
                        <div class="match-action-menu hidden absolute right-0 mt-1 w-40 origin-top-right bg-white dark:bg-gray-700 rounded-md shadow-lg ring-1 ring-black dark:ring-white ring-opacity-5 focus:outline-none z-20" role="menu" aria-orientation="vertical" data-match-id="${match.id}">
                            <div class="py-1" role="none">
                                <button type="button" class="menu-delete-match-btn text-red-600 dark:text-red-400 group flex items-center w-full px-4 py-2 text-sm text-left hover:bg-red-50 dark:hover:bg-red-600/50 hover:text-red-700 dark:hover:text-red-300" role="menuitem" data-match-id="${match.id}">
                                    <svg class="mr-3 h-5 w-5 text-red-400 dark:text-red-500 group-hover:text-red-500 dark:group-hover:text-red-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd" /></svg>
                                    Delete Match
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Unified Footer Section -->
            <div class="border-t border-gray-200 dark:border-gray-700/50 pt-3 mt-auto space-y-3">
                ${opponentsHtml}
                
                <div class="flex flex-wrap items-center gap-1.5 min-h-[28px] tags-container">
                    ${tagPillsHtml}
                    ${addTagButtonHtml}
                </div>
            </div>
        `;
        fragment.appendChild(card);
    });

    containerElement.appendChild(fragment);
}

async function updateMatchHistoryView() {
    const matchesListContainer = document.getElementById("matches-list-items");
    const noMatchesMessage = document.getElementById("no-matches-message-history");

    if (!matchesListContainer || !noMatchesMessage) {
        console.error("Required match list elements not found (matches-list-items or no-matches-message-history).");
        return;
    }

    matchesListContainer.innerHTML = `<div class="p-6 text-center text-gray-500 dark:text-gray-400 md:col-span-2"><svg class="animate-spin h-6 w-6 text-violet-500 dark:text-violet-400 mx-auto mb-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>Loading match history...</div>`;
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
            try { const errorData = await response.json(); errorMsg = errorData.error || errorMsg; } catch (e) { /* Ignore */ }
            throw new Error(errorMsg);
        }

        const userMatches = await response.json();
        if (!Array.isArray(userMatches)) throw new Error("Invalid data format from server.");

        displayMatches(userMatches, matchesListContainer, noMatchesMessage);

        if (userMatches.length > 0) {
            initializeMatchActionMenus("matches-list-items", updateMatchHistoryView);
        }

    } catch (error) {
        console.error("Failed to fetch or display match history:", error);
        displayMatches([], matchesListContainer, noMatchesMessage); 
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const matchesContainer = document.getElementById('matches-list-items');
    const quickAddModal = document.getElementById("quickAddTagModal");
    const quickAddModalCloseBtn = document.getElementById("quickAddTagModalCloseButton");
    const quickAddModalDoneBtn = document.getElementById("quickAddTagModalDoneButton");

    if (matchesContainer) {
        updateMatchHistoryView(); 

        matchesContainer.addEventListener('click', async (event) => {
            const removeButton = event.target.closest('.remove-match-tag-button');
            const addButton = event.target.closest('.add-match-tag-button');

            if (removeButton) {
                const removedSuccessfully = await handleRemoveMatchTagClick(event);
                if (removedSuccessfully) {
                    updateMatchHistoryView();
                }
            } else if (addButton) {
                event.preventDefault();
                event.stopPropagation();
                const matchId = addButton.dataset.matchId;
                if (matchId && typeof openQuickAddTagModal === 'function') {
                    openQuickAddTagModal(matchId, 'match', updateMatchHistoryView);
                } else {
                    console.error("Cannot open tag modal: Missing matchId or modal function.");
                }
            }
        });
    } else {
        console.warn("Match list container #matches-list-items not found.");
    }

    if (quickAddModal && quickAddModalCloseBtn && quickAddModalDoneBtn && typeof closeQuickAddTagModal === 'function') {
        quickAddModalCloseBtn.addEventListener('click', closeQuickAddTagModal);
        quickAddModalDoneBtn.addEventListener('click', closeQuickAddTagModal);
        quickAddModal.addEventListener('click', (event) => {
            if (event.target === quickAddModal) { 
                closeQuickAddTagModal();
            }
        });
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape' && quickAddModal && !quickAddModal.classList.contains('hidden')) {
                closeQuickAddTagModal();
            }
        });
    } else {
         console.warn("Quick Add Tag Modal elements (quickAddTagModal, quickAddTagModalCloseButton, quickAddTagModalDoneButton) or closeQuickAddTagModal function not fully available on matches-history.html.");
    }

    window.refreshMatchHistory = updateMatchHistoryView;
});

export { updateMatchHistoryView, displayMatches, handleRemoveMatchTagClick };