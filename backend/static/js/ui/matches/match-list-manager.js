// backend/static/js/ui/matches/match-list-manager.js

import { authFetch } from '../../auth/auth.js';
import { formatMatchResult } from '../../utils.js';
import { openQuickAddTagModal } from '../tag-utils.js';
import { initializeMatchActionMenus } from './match-actions.js';
// import { showFlashMessage } from '../../utils.js'; // Optional

// --- CSRF Token Helper ---
async function getCsrfToken() {
    try {
        const response = await authFetch('/api/auth/csrf_token');
        if (!response) throw new Error("Network or Auth Error fetching CSRF token.");
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || `Failed to fetch CSRF token: ${response.status}`);
        }
        const data = await response.json();
        if (!data.csrf_token) throw new Error("CSRF token not found in response.");
        return data.csrf_token;
    } catch (error) {
        console.error("Error getting CSRF token:", error);
        if (typeof showFlashMessage === 'function') {
            showFlashMessage("Could not verify security token. Please try logging in again.", "danger");
        }
        throw error;
    }
}

// --- Helper Functions ---

function getSelectedMatchTagIds() {
    const optionsContainer = document.getElementById("match-tag-filter-options");
    const selectedIds = [];
    if (!optionsContainer) return selectedIds;
    const checkedBoxes = optionsContainer.querySelectorAll('input[type="checkbox"]:checked');
    checkedBoxes.forEach(checkbox => {
        if (checkbox.value && checkbox.value.trim() !== "") {
            selectedIds.push(checkbox.value);
        }
    });
    return selectedIds;
}

async function handleRemoveMatchTagClick(event) {
    const removeButton = event.target.closest('.remove-match-tag-button');
    if (!removeButton) return;

    event.preventDefault();
    event.stopPropagation();

    const tagPill = removeButton.closest('.tag-pill');
    const cardElement = removeButton.closest('.match-item');

    if (!tagPill || !cardElement) return;

    const tagId = tagPill.dataset.tagId;
    const matchId = cardElement.dataset.matchId;

    if (!tagId || !matchId) {
         if (typeof showFlashMessage === 'function') showFlashMessage("Could not remove tag: IDs missing.", "danger");
        return;
    }

    removeButton.disabled = true;
    tagPill.style.opacity = '0.5';

    try {
        const csrfToken = await getCsrfToken();
        const response = await authFetch(`/api/matches/${matchId}/tags/${tagId}`, {
            method: 'DELETE',
            headers: { 'X-CSRF-TOKEN': csrfToken }
        });

        if (!response) throw new Error("Authentication or network error.");

        if (response.ok) {
            tagPill.remove();
             if (typeof showFlashMessage === 'function') showFlashMessage("Tag removed successfully.", "success");
        } else {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || `Failed to remove tag (${response.status})`);
        }
    } catch (error) {
        console.error("Error removing match tag:", error);
        if (typeof showFlashMessage === 'function') showFlashMessage(error.message || "Could not remove tag.", "danger");
        if (document.body.contains(removeButton)) removeButton.disabled = false;
        if (document.body.contains(tagPill)) tagPill.style.opacity = '1';
    }
}


// --- Display Logic ---

function displayMatches(matches, containerElement, noMatchesElement) {
    if (!containerElement) return;

    containerElement.innerHTML = "";
    if (noMatchesElement) noMatchesElement.classList.add('hidden');

    if (!matches || !Array.isArray(matches) || matches.length === 0) {
        if (noMatchesElement) {
            noMatchesElement.textContent = "No matches found matching the criteria.";
            noMatchesElement.classList.remove('hidden');
        } else {
            containerElement.innerHTML = `<div class="text-center text-violet-500 mt-4 p-4 text-base border border-dashed border-violet-300 rounded-lg md:col-span-2">No matches found.</div>`;
        }
        return;
    }

    const fragment = document.createDocumentFragment();
    const locale = navigator.language || 'en-US';
    const dateOptions = { month: 'short', day: 'numeric', year: 'numeric', hour: 'numeric', minute: '2-digit', hour12: true };

    matches.forEach(match => {
        const card = document.createElement("div");
        card.className = `match-item relative bg-white shadow-md rounded-xl border border-gray-200 p-3 hover:shadow-lg transition-all duration-200 ease-in-out`;
        card.dataset.matchId = match.id;

        // --- Data points ---
        const deckName = match.deck?.name ?? 'Unknown Deck';
        const deckTypeName = match.deck_type?.name ?? 'Unknown Format';
        const escapedDeckName = deckName.replace(/"/g, '"');
        let formattedDate = 'N/A';
        if (match.date) {
            try {
                formattedDate = new Date(match.date).toLocaleString(locale, dateOptions);
            } catch (e) { formattedDate = match.date; }
        }

        // --- Result Badge Styling ---
        const resultText = formatMatchResult(match.result);
        const lowerResult = resultText.toLowerCase();
        let resultBadgeClass = 'bg-gray-400 text-white';
        if (lowerResult === 'win') { resultBadgeClass = 'bg-green-500 text-white'; }
        else if (lowerResult === 'loss') { resultBadgeClass = 'bg-red-500 text-white'; }
        else if (lowerResult === 'draw') { resultBadgeClass = 'bg-yellow-500 text-white'; }
        const resultBadgeHtml = `<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${resultBadgeClass}">${resultText}</span>`;

        // --- Deck Type Badge Styling ---
        const deckTypeBadgeClass = 'bg-violet-500 text-white';
        const deckTypeBadgeHtml = `<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${deckTypeBadgeClass}">${deckTypeName}</span>`;

        // --- Tags Section ---
        let tagPillsHtml = '';
        if (match.tags && match.tags.length > 0) {
            tagPillsHtml = match.tags.map(tag => {
                const escapedTagName = tag.name.replace(/"/g, '"');
                return `<span class="tag-pill inline-flex items-center gap-1 bg-violet-100 text-violet-800 text-xs font-medium px-2 py-0.5 rounded-md mr-1 mb-1" data-tag-id="${tag.id}">
                    ${tag.name}
                    <button type="button" class="remove-match-tag-button ml-0.5 text-violet-500 hover:text-violet-700 font-bold focus:outline-none" aria-label="Remove tag ${escapedTagName} from match">×</button>
                </span>`;
            }).join('');
        }
        const addTagButtonHtml = `<button type="button" class="add-match-tag-button inline-flex items-center text-xs font-medium px-2 py-0.5 rounded border border-dashed border-gray-400 text-gray-500 hover:bg-gray-100 hover:text-gray-700 hover:border-solid mb-1" aria-label="Add tag to match" data-match-id="${match.id}">+ Tag</button>`;
        const tagsContainerHtml = `<div class="mt-2 flex flex-wrap items-center gap-x-1 tags-container">${tagPillsHtml}${addTagButtonHtml}</div>`;

        // --- Action Menu HTML Structure ---
        const actionMenuHtml = `
            <div class="relative match-actions flex-shrink-0">
                <button type="button" class="match-options-btn p-1 rounded-full text-gray-400 hover:bg-gray-100 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-violet-500" data-match-id="${match.id}" aria-label="Match options" aria-haspopup="true" aria-expanded="false">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5 pointer-events-none"><path stroke-linecap="round" stroke-linejoin="round" d="M12 6.75a.75.75 0 1 1 0-1.5.75.75 0 0 1 0 1.5ZM12 12.75a.75.75 0 1 1 0-1.5.75.75 0 0 1 0 1.5ZM12 18.75a.75.75 0 1 1 0-1.5.75.75 0 0 1 0 1.5Z" /></svg>
                </button>
                <div class="match-action-menu hidden absolute right-0 mt-1 w-40 origin-top-right bg-white rounded-md shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none z-20" role="menu" aria-orientation="vertical" data-match-id="${match.id}">
                    <div class="py-1" role="none">
                        <button type="button" class="menu-delete-match-btn text-red-600 group flex items-center w-full px-4 py-2 text-sm text-left hover:bg-red-50 hover:text-red-700" role="menuitem" data-match-id="${match.id}">
                            <svg class="mr-3 h-5 w-5 text-red-400 group-hover:text-red-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd" /></svg>
                            Delete Match
                        </button>
                    </div>
                </div>
            </div>`;


        // --- Card Layout Assembly (Aligning Right Edges) ---
        card.innerHTML = `
            <div class="flex justify-between gap-4">
                <div class="flex-grow min-w-0">
                    <h3 class="text-lg font-bold text-gray-800 break-words leading-tight truncate overflow-hidden" title="${escapedDeckName}">
                        ${deckName}
                    </h3>
                    <p class="text-xs text-gray-500 mt-0.5">
                        ${formattedDate}
                    </p>
                </div>

                <div class="flex flex-col items-end flex-shrink-0 space-y-1">
                    <div class="flex items-center gap-1">
                        ${resultBadgeHtml}
                        ${actionMenuHtml}
                    </div>
                    ${deckTypeBadgeHtml}
                </div>
            </div>

            ${tagsContainerHtml}
        `;

        fragment.appendChild(card);
    });

    containerElement.appendChild(fragment);
}


// --- Data Fetching and View Update ---

let currentFilters = {};

async function updateMatchHistoryView(filters = currentFilters) {
    currentFilters = filters;
    const matchesListContainer = document.getElementById("matches-list-items");
    const noMatchesMessage = document.getElementById("no-matches-message-history");

    if (!matchesListContainer || !noMatchesMessage) return;

    matchesListContainer.innerHTML = `<div class="p-6 text-center text-violet-500 md:col-span-2">Loading match history...</div>`;
    noMatchesMessage.classList.add('hidden');

    const params = new URLSearchParams();
    if (filters.tags && Array.isArray(filters.tags) && filters.tags.length > 0) {
        params.append('tags', filters.tags.join(','));
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
        if (!Array.isArray(userMatches)) throw new Error("Received invalid data format from server.");

        displayMatches(userMatches, matchesListContainer, noMatchesMessage);

        if (userMatches.length > 0) {
            initializeMatchActionMenus("matches-list-items");
        }

    } catch (error) {
        console.error("Failed to fetch or process match history:", error);
         if (typeof showFlashMessage === 'function') { showFlashMessage(error.message || "An unexpected error occurred loading history.", "danger"); }
        displayMatches([], matchesListContainer, noMatchesMessage);
    }
}


// --- Initialization ---

document.addEventListener('DOMContentLoaded', () => {
    const matchesContainer = document.getElementById('matches-list-items');
    if (!matchesContainer) return;

    updateMatchHistoryView(); // Initial load

    matchesContainer.addEventListener('click', (event) => {
        if (event.target.closest('.remove-match-tag-button')) {
            handleRemoveMatchTagClick(event);
        } else if (event.target.closest('.add-match-tag-button')) {
            const addButton = event.target.closest('.add-match-tag-button');
            event.preventDefault();
            event.stopPropagation();
            const matchId = addButton.dataset.matchId;
            if (matchId && typeof openQuickAddTagModal === 'function') {
                openQuickAddTagModal(matchId, 'match', () => updateMatchHistoryView(currentFilters));
            } else {
                console.error("Add tag button missing matchId or modal function unavailable.");
                if(typeof showFlashMessage === 'function') showFlashMessage("Cannot open tag modal.", "warning");
            }
        }
    });

    window.refreshMatchHistory = updateMatchHistoryView;

});

// --- Exports ---
export { updateMatchHistoryView, displayMatches, handleRemoveMatchTagClick };