// backend/static/js/ui/decks/deck-details.js 

import { authFetch } from '../../auth/auth.js';
import { openQuickAddTagModal, closeQuickAddTagModal } from '../tag-utils.js';
import { loadDeckMatchesIntoContainer } from '../matches/deck-matches.js'; 
import { openLogMatchModal } from '../matches/log-match-modal.js';

let currentDeckId = null;
let currentDeckName = null; 

let deckDetailsContentElement = null;
let deckDetailsLoadingElement = null;
let deckPageTitleElement = null;
let backToDecksButton = null;

let deckInfoStatsCardElement = null;
let quickLogCardElement = null;
let deckTagsCardElement = null;
let turnOrderStatsCardElement = null;
let recentMatchesCardElement = null;
let mulliganStatsCardElement = null; // New element for mulligan stats

let deckOptionsMenuButton = null;
let deckOptionsDropdown = null;
let renameDeckButton = null;
let deleteDeckButton = null;

let renameDeckModalElement = null;
let renameDeckFormElement = null;
let renameDeckModalCloseButton = null;
let renameDeckCancelButton = null;
let newDeckNameInputElement = null;

let globalLogMatchFab = null;

// --- UI Update Functions ---
function updatePageTitle(newTitle) {
    document.title = `TCG Tracker: ${newTitle || 'Deck Details'}`;
    if (deckPageTitleElement) {
        deckPageTitleElement.textContent = newTitle || "Deck Details";
    }
}

function showLoadingState() {
    if (deckDetailsLoadingElement) deckDetailsLoadingElement.style.display = 'block';
    // Add the new mulligan card to the list of elements to hide
    [deckInfoStatsCardElement, quickLogCardElement, deckTagsCardElement, turnOrderStatsCardElement, recentMatchesCardElement, mulliganStatsCardElement]
        .forEach(el => el?.classList.add('hidden'));
}

function hideLoadingState() {
    if (deckDetailsLoadingElement) deckDetailsLoadingElement.style.display = 'none';
}

// --- Card Rendering Functions ---

function renderDeckInfoStats(deckData) {
    if (!deckInfoStatsCardElement || !deckData) return;

    const winRate = parseFloat(deckData.win_rate ?? 0);
    const totalMatches = parseInt(deckData.total_matches ?? 0, 10);
    let winrateColorClass = 'text-gray-700 dark:text-gray-200';
    if (totalMatches > 0) {
        if (winRate >= 55) winrateColorClass = 'text-green-500 dark:text-green-400';
        else if (winRate < 45) winrateColorClass = 'text-red-500 dark:text-red-400';
        else winrateColorClass = 'text-yellow-500 dark:text-yellow-400';
    }

    let commanderHtml = '';
    if (deckData.commander_name) {
        commanderHtml += `
            <div class="py-2.5 sm:py-3 grid grid-cols-3 gap-4 px-4 sm:px-5">
                <dt class="text-xs font-medium text-gray-500 dark:text-gray-400">Commander</dt>
                <dd class="mt-0 text-xs text-gray-900 dark:text-gray-100 col-span-2">${deckData.commander_name}</dd>
            </div>`;
    }
    
    let assocLabel = "Associated";
    if (deckData.partner_name) assocLabel = "Partner";
    else if (deckData.friends_forever_name) assocLabel = "Friends Forever";
    else if (deckData.background_name) assocLabel = "Background";
    else if (deckData.doctor_companion_name) assocLabel = "Companion";
    else if (deckData.time_lord_doctor_name) assocLabel = "Doctor";    
    
    if (deckData.associated_commander_name) {
        commanderHtml += `
            <div class="py-2.5 sm:py-3 grid grid-cols-3 gap-4 px-4 sm:px-5 ${commanderHtml ? 'bg-gray-50/70 dark:bg-gray-700/40' : ''}">
                <dt class="text-xs font-medium text-gray-500 dark:text-gray-400">${assocLabel}</dt>
                <dd class="mt-0 text-xs text-gray-900 dark:text-gray-100 col-span-2">${deckData.associated_commander_name}</dd>
            </div>`;
    }
    
    deckInfoStatsCardElement.innerHTML = `
        <div class="border-t border-gray-200 dark:border-gray-700 first:border-t-0">
            <dl class="divide-y divide-gray-200 dark:divide-gray-700">
                ${commanderHtml}
                <div class="py-3 sm:py-4 grid grid-cols-3 gap-4 px-4 sm:px-5 ${commanderHtml ? 'bg-gray-50/70 dark:bg-gray-700/40' : ''}">
                    <dt class="text-sm font-semibold text-gray-600 dark:text-gray-300 self-center">Performance</dt>
                    <dd class="mt-0 text-gray-900 dark:text-gray-100 col-span-2 self-center text-right sm:text-left">
                        <span class="${winrateColorClass} text-xl font-bold">${winRate.toFixed(1)}%</span>
                        <span class="ml-1 text-xs text-gray-500 dark:text-gray-400">WR</span>
                        <span class="mx-1.5 text-gray-300 dark:text-gray-600">|</span>
                        <span class="text-sm">${totalMatches} M / ${deckData.total_wins ?? 0} W</span>
                    </dd>
                </div>
            </dl>
        </div>
    `;
    deckInfoStatsCardElement.classList.remove('hidden');
}

function renderQuickLogButtons() {
    if (!quickLogCardElement) return;
    const container = quickLogCardElement.querySelector('#quick-log-buttons-container');
    if (!container) return;

    container.innerHTML = `
        <button type="button" data-result="0" class="quick-log-btn bg-green-500 hover:bg-green-600 text-white font-medium py-2 px-4 rounded-lg shadow-sm transition w-full text-sm">Win</button>
        <button type="button" data-result="1" class="quick-log-btn bg-red-500 hover:bg-red-600 text-white font-medium py-2 px-4 rounded-lg shadow-sm transition w-full text-sm">Loss</button>
        <button type="button" data-result="2" class="quick-log-btn bg-yellow-500 hover:bg-yellow-600 text-white font-medium py-2 px-4 rounded-lg shadow-sm transition w-full text-sm">Draw</button>
    `;
    quickLogCardElement.classList.remove('hidden');
}

function renderDeckTags(tags, deckId) {
    if (!deckTagsCardElement) return;
    const pillsContainer = deckTagsCardElement.querySelector('#deck-tags-pills-container-detail');
    const addButton = deckTagsCardElement.querySelector('#add-deck-tag-button-detail');

    if (!pillsContainer || !addButton) return;

    pillsContainer.innerHTML = ''; 
    if (tags && tags.length > 0) {
        tags.forEach(tag => {
            const pill = document.createElement('span');
            pill.className = 'tag-pill inline-flex items-center gap-1 bg-violet-100 dark:bg-violet-700/60 text-violet-700 dark:text-violet-300 text-xs font-medium px-2 py-0.5 rounded-full';
            pill.dataset.tagId = tag.id;
            pill.innerHTML = `
                <span>${tag.name}</span>
                <button type="button" class="remove-deck-tag-button ml-0.5 -mr-0.5 flex-shrink-0 rounded-full p-0.5 text-violet-400 dark:text-violet-500 hover:bg-violet-200 dark:hover:bg-violet-600" aria-label="Remove tag ${tag.name}">
                    <svg class="h-2 w-2" stroke="currentColor" fill="none" viewBox="0 0 8 8"><path stroke-linecap="round" stroke-width="1.5" d="M1 1l6 6m0-6L1 7" /></svg>
                </button>
            `;
            pillsContainer.appendChild(pill);
        });
    } else {
        pillsContainer.innerHTML = `<span class="text-xs text-gray-500 dark:text-gray-400 italic">No tags yet.</span>`;
    }
    deckTagsCardElement.classList.remove('hidden');
}

function renderTurnOrderStats(stats) {
    if (!turnOrderStatsCardElement || !stats) return;
    const container = turnOrderStatsCardElement.querySelector('#turn-order-stats-container');
    if (!container) return;

    container.innerHTML = '';
    const positions = ["1st", "2nd", "3rd", "4th"];
    let hasAnyStats = false;
    positions.forEach((posText, index) => {
        const posKey = String(index + 1);
        const posData = stats[posKey];
        const div = document.createElement('div');
        div.className = 'p-2 bg-gray-50 dark:bg-gray-700/50 rounded-md text-center';
        if (posData && posData.matches > 0) {
            hasAnyStats = true;
            const winRate = parseFloat(posData.win_rate ?? 0).toFixed(0);
            let color = 'text-gray-700 dark:text-gray-200';
            if (parseFloat(winRate) >= 55) color = 'text-green-500 dark:text-green-400';
            else if (parseFloat(winRate) < 45) color = 'text-red-500 dark:text-red-400';
            else color = 'text-yellow-500 dark:text-yellow-400';

            div.innerHTML = `
                <div class="font-medium text-gray-600 dark:text-gray-300">${posText}</div>
                <div class="text-base font-semibold ${color}">${winRate}%</div>
                <div class="text-xxs text-gray-400 dark:text-gray-500">(${posData.wins}/${posData.matches})</div>
            `;
        } else {
            div.innerHTML = `
                <div class="font-medium text-gray-600 dark:text-gray-300">${posText}</div>
                <div class="text-base text-gray-400 dark:text-gray-500">-</div>
                <div class="text-xxs text-gray-400 dark:text-gray-500">(0/0)</div>
            `;
        }
        container.appendChild(div);
    });

    if (!hasAnyStats) { 
        container.innerHTML = `<p class="col-span-full text-xs text-gray-500 dark:text-gray-400 italic text-center py-2">No match data with turn order logged yet.</p>`;
    }
    turnOrderStatsCardElement.classList.remove('hidden');
}

// --- NEW FUNCTION ---
function renderMulliganStats(stats) {
    const container = mulliganStatsCardElement;
    if (!container) return;

    const tableBody = container.querySelector('#mulligan-stats-tbody');
    const noDataMessage = container.querySelector('#no-mulligan-data');
    const table = tableBody ? tableBody.closest('table') : null;

    if (!tableBody || !noDataMessage || !table) {
        container.classList.add('hidden'); // Hide card if internal structure is missing
        return;
    }

    tableBody.innerHTML = ''; // Clear previous data

    if (stats && stats.length > 0) {
        stats.forEach(stat => {
            const winRate = stat.win_rate;
            let textColor = 'text-gray-600 dark:text-gray-300';
            if (stat.game_count > 0) {
                if (winRate >= 55) textColor = 'text-green-600 dark:text-green-400';
                else if (winRate < 45) textColor = 'text-red-600 dark:text-red-400';
                else textColor = 'text-yellow-500 dark:text-yellow-400';
            }

            const row = `
                <tr>
                    <td class="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-gray-100">
                        ${stat.label}
                    </td>
                    <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400 text-center">
                        ${stat.game_count}
                    </td>
                    <td class="px-4 py-3 whitespace-nowrap text-sm font-semibold ${textColor} text-center">
                        ${winRate}%
                    </td>
                </tr>
            `;
            tableBody.insertAdjacentHTML('beforeend', row);
        });

        table.classList.remove('hidden');
        noDataMessage.classList.add('hidden');
        container.classList.remove('hidden');
    } else {
        // No data, so ensure the entire card is hidden for a cleaner look
        container.classList.add('hidden');
    }
}

function renderRecentMatches(matches, deckId) {
    if (!recentMatchesCardElement) return;
    const listContainer = recentMatchesCardElement.querySelector('#recent-matches-list-container');
    const noMatchesMsg = recentMatchesCardElement.querySelector('#no-recent-matches-message');
    const viewAllBtnContainer = recentMatchesCardElement.querySelector('#view-all-matches-button-container');
    const viewAllLink = recentMatchesCardElement.querySelector('#view-all-matches-link');

    if (!listContainer || !noMatchesMsg || !viewAllBtnContainer || !viewAllLink) {
        console.error("One or more elements for recent matches not found.");
        return;
    }

    listContainer.innerHTML = '';
    if (matches && matches.length > 0) {
        noMatchesMsg.classList.add('hidden');
        matches.forEach(match => {
            const item = document.createElement('div');
            item.className = 'py-2 border-b border-gray-100 dark:border-gray-700/50 last:border-b-0 flex justify-between items-center text-xs';
            const resultText = match.result === 0 ? 'Win' : match.result === 1 ? 'Loss' : 'Draw';
            const resultColor = match.result === 0 ? 'text-green-500' : match.result === 1 ? 'text-red-500' : 'text-yellow-500';
            const date = match.date ? new Date(match.date).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' }) : 'N/A';
            item.innerHTML = `
                <span class="font-medium ${resultColor}">${resultText}</span>
                <span class="text-gray-400 dark:text-gray-500">${date} (P${match.player_position || '?'})</span>
            `;
            listContainer.appendChild(item);
        });
        if (matches.length >= 5 && currentDeckId) { 
            viewAllLink.href = `/matches-history?deckFilters=${currentDeckId}`; 
            viewAllBtnContainer.style.display = 'block';
        } else {
            viewAllBtnContainer.style.display = 'none';
        }
    } else {
        noMatchesMsg.classList.remove('hidden');
        viewAllBtnContainer.style.display = 'none';
    }
    recentMatchesCardElement.classList.remove('hidden');
}


async function loadDeckDetails(deckIdToLoad) {
    showLoadingState();
    currentDeckId = deckIdToLoad; 

    try {
        // Update API call to explicitly request all stats we need
        const response = await authFetch(`/api/decks/${deckIdToLoad}?include_turn_stats=true&include_recent_matches=5&include_mulligan_stats=true`);
        if (!response) throw new Error("Auth/Network Error fetching deck details.");
        if (!response.ok) {
            if (response.status === 404) throw new Error("Deck not found.");
            const errorData = await response.json().catch(() => ({ message: `Error loading deck details (${response.status})` }));
            throw new Error(errorData.error || errorData.message || `HTTP error ${response.status}`);
        }
        const deckData = await response.json();
        if (!deckData || !deckData.id) throw new Error("Received invalid deck data.");

        currentDeckName = deckData.name;
        updatePageTitle(deckData.name);

        renderDeckInfoStats(deckData);
        renderQuickLogButtons(); 
        renderDeckTags(deckData.tags, deckData.id); 
        renderTurnOrderStats(deckData.turn_order_stats || {});
        renderMulliganStats(deckData.mulligan_stats || []); // Call new function
        renderRecentMatches(deckData.recent_matches || [], deckData.id); 
        
        setupDeckOptionsMenuListeners(deckData);

    } catch(error) {
        console.error("[deck-details.js] Error in loadDeckDetails:", error);
        if (typeof showFlashMessage === 'function') showFlashMessage(error.message || "Failed to load deck details.", "danger");
        if (deckDetailsContentElement) deckDetailsContentElement.innerHTML = `<div class="p-6 text-center text-red-500 dark:text-red-400">${error.message || 'Error loading details.'}</div>`;
        updatePageTitle("Error");
    } finally {
        hideLoadingState();
    }
}

// --- Event Listeners & Actions ---
function setupDeckOptionsMenuListeners(deck) {
    if (!deckOptionsMenuButton || !deckOptionsDropdown || !renameDeckButton || !deleteDeckButton) return;

    deckOptionsMenuButton.onclick = (event) => {
        event.stopPropagation();
        deckOptionsDropdown.classList.toggle('hidden');
        deckOptionsMenuButton.setAttribute('aria-expanded', deckOptionsDropdown.classList.contains('hidden') ? 'false' : 'true');
    };
    renameDeckButton.onclick = () => {
        deckOptionsDropdown.classList.add('hidden');
        promptForRename(deck.id, deck.name);
    };
    deleteDeckButton.onclick = () => {
        deckOptionsDropdown.classList.add('hidden');
        showDeleteConfirmation(deck.id, deck.name);
    };
}

function promptForRename(deckId, currentName) {
    if (!renameDeckModalElement || !newDeckNameInputElement || !renameDeckFormElement || !renameDeckModalCloseButton || !renameDeckCancelButton) return;
    
    newDeckNameInputElement.value = currentName;
    renameDeckModalElement.classList.remove('hidden');
    setTimeout(() => newDeckNameInputElement.focus(), 50);

    renameDeckFormElement.onsubmit = async (e) => {
        e.preventDefault();
        const newName = newDeckNameInputElement.value.trim();
        if (newName && newName !== currentName) {
            await updateDeckNameOnServer(deckId, newName);
        }
        closeRenameModal();
    };
    renameDeckModalCloseButton.onclick = closeRenameModal;
    renameDeckCancelButton.onclick = closeRenameModal;
    renameDeckModalElement.addEventListener('click', (event) => {
        if (event.target === renameDeckModalElement) closeRenameModal();
    });
}

function closeRenameModal() {
    if (renameDeckModalElement) renameDeckModalElement.classList.add('hidden');
    if (renameDeckFormElement) renameDeckFormElement.onsubmit = null;
}

async function updateDeckNameOnServer(deckId, newName) {
    try {
        const response = await authFetch(`/api/decks/${deckId}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ deck_name: newName })
        });
        if (response.ok) {
            if (typeof showFlashMessage === 'function') showFlashMessage("Deck renamed successfully!", "success");
            loadDeckDetails(deckId); 
        } else {
            const errorData = await response.json().catch(() => ({}));
            if (typeof showFlashMessage === 'function') showFlashMessage(`Error renaming deck: ${errorData.error || response.statusText}`, "danger");
        }
    } catch (error) {
        if (typeof showFlashMessage === 'function') showFlashMessage(error.message || 'Network error. Please try again.', "danger");
    }
}

function showDeleteConfirmation(deckId, deckName) {
     if (window.confirm(`Are you sure you want to delete the deck "${deckName}"? This action cannot be undone.`)) {
        deleteDeckOnServer(deckId);
    }
}

async function deleteDeckOnServer(deckId) {
    try {
        const response = await authFetch(`/api/decks/${deckId}`, {
            method: 'DELETE',
        });
        if (response.ok) {
            if (typeof showFlashMessage === 'function') showFlashMessage("Deck deleted successfully. Redirecting...", "success");
            setTimeout(() => { window.location.href = '/my-decks'; }, 1500);
        } else {
            const errorData = await response.json().catch(() => ({}));
            const message = errorData.error || errorData.msg || `Failed to delete deck (${response.statusText})`;
            if (typeof showFlashMessage === 'function') showFlashMessage(message, "danger");
        }
    } catch (error) {
        if (typeof showFlashMessage === 'function') showFlashMessage(error.message || 'Network error. Please try again.', "danger");
    }
}

function initializePageEventListeners() {
    if (quickLogCardElement) {
        quickLogCardElement.addEventListener('click', (event) => {
            const button = event.target.closest('.quick-log-btn');
            if (button && currentDeckId && currentDeckName) {
                const resultValue = button.dataset.result;
                if (typeof openLogMatchModal === 'function') {
                    openLogMatchModal({ id: currentDeckId, name: currentDeckName, result: parseInt(resultValue, 10) });
                }
            }
        });
    }

    if (deckTagsCardElement) {
        deckTagsCardElement.addEventListener('click', async (event) => {
            const addButton = event.target.closest('#add-deck-tag-button-detail');
            const removeButton = event.target.closest('.remove-deck-tag-button');

            if (addButton && currentDeckId) {
                if (typeof openQuickAddTagModal === 'function') {
                    openQuickAddTagModal(currentDeckId, 'deck', () => loadDeckDetails(currentDeckId));
                }
            } else if (removeButton && currentDeckId) {
                const tagPill = removeButton.closest('.tag-pill');
                const tagId = tagPill?.dataset.tagId;
                if (!tagId) return;
                try {
                    const response = await authFetch(`/api/decks/${currentDeckId}/tags/${tagId}`, { method: 'DELETE' });
                    if (response.ok) loadDeckDetails(currentDeckId);
                    else { 
                        const err = await response.json().catch(() => ({error: "Failed to remove tag"}));
                        if(typeof showFlashMessage === 'function') showFlashMessage(err.error || "Could not remove tag.", "danger");
                    }
                } catch (err) { 
                    console.error("Error removing tag:", err);
                    if(typeof showFlashMessage === 'function') showFlashMessage("Could not remove tag.", "danger");
                }
            }
        });
    }

    if (backToDecksButton) {
        backToDecksButton.addEventListener('click', () => {
            if (document.referrer && new URL(document.referrer).pathname.includes('/my-decks')) {
                window.history.back();
            } else {
                window.location.href = '/my-decks';
            }
        });
    }

    if (globalLogMatchFab) {
        globalLogMatchFab.addEventListener('click', () => {
            if (typeof openLogMatchModal === 'function') {
                openLogMatchModal();
            }
        });
    }
    
    document.addEventListener('click', (event) => {
        if (deckOptionsMenuButton && deckOptionsDropdown && 
            !deckOptionsMenuButton.contains(event.target) && 
            !deckOptionsDropdown.contains(event.target)) {
            deckOptionsDropdown.classList.add('hidden');
            deckOptionsMenuButton.setAttribute('aria-expanded', 'false');
        }
    });
}

document.addEventListener("DOMContentLoaded", () => {
    deckPageTitleElement = document.getElementById("deck-page-title");
    deckDetailsContentElement = document.getElementById("deck-details-content");
    deckDetailsLoadingElement = document.getElementById('deck-details-loading');
    backToDecksButton = document.getElementById('back-to-decks-btn');
    
    deckInfoStatsCardElement = document.getElementById('deck-info-stats-card');
    quickLogCardElement = document.getElementById('quick-log-card');
    deckTagsCardElement = document.getElementById('deck-tags-card');
    turnOrderStatsCardElement = document.getElementById('turn-order-stats-card');
    recentMatchesCardElement = document.getElementById('recent-matches-card');
    mulliganStatsCardElement = document.getElementById('mulligan-stats-container'); // Initialize new element

    deckOptionsMenuButton = document.getElementById('deck-options-menu-button');
    deckOptionsDropdown = document.getElementById('deck-options-dropdown');
    renameDeckButton = document.getElementById('rename-deck-button'); 
    deleteDeckButton = document.getElementById('delete-deck-button'); 

    renameDeckModalElement = document.getElementById('renameDeckModal');
    renameDeckFormElement = document.getElementById('rename-deck-form');
    renameDeckModalCloseButton = document.getElementById('renameDeckModalCloseButton');
    renameDeckCancelButton = document.getElementById('renameDeckCancelButton');
    newDeckNameInputElement = document.getElementById('new_deck_name');

    globalLogMatchFab = document.getElementById('globalLogMatchFab');

    if (!deckDetailsContentElement) return; 

    const pathParts = window.location.pathname.split("/");
    const idSlug = pathParts[pathParts.length - 1];
    let deckIdToLoad;

    try {
        const potentialId = idSlug.match(/^(\d+)/);
        if (potentialId && potentialId[1]) {
            deckIdToLoad = parseInt(potentialId[1], 10);
            if (isNaN(deckIdToLoad)) throw new Error("Parsed Deck ID is NaN from slug.");
        } else {
            throw new Error("No numeric ID found in URL slug.");
        }
    } catch(e) {
         console.error("Invalid Deck ID in URL:", idSlug, e);
         if (typeof showFlashMessage === 'function') showFlashMessage("Invalid Deck ID in URL.", "danger");
         if (deckDetailsContentElement) deckDetailsContentElement.innerHTML = '<div class="p-6 text-center text-red-500 dark:text-red-400">Invalid Deck ID in URL.</div>';
         updatePageTitle("Invalid Deck");
         return;
     }

    if (deckIdToLoad) {
        loadDeckDetails(deckIdToLoad);
        initializePageEventListeners(); 
    } else {
        console.error("[deck-details.js] Deck ID could not be determined. Cannot load details.");
        if (deckDetailsContentElement) deckDetailsContentElement.innerHTML = '<div class="p-6 text-center text-red-500 dark:text-red-400">Could not determine Deck ID.</div>';
        updatePageTitle("Error");
    }
    
    document.addEventListener('globalMatchLoggedSuccess', (event) => {
        if (currentDeckId && event.detail && typeof event.detail.deckId !== 'undefined') {
            const eventDeckId = parseInt(event.detail.deckId, 10);
            if (eventDeckId === currentDeckId) {
                console.log("[deck-details.js] Refreshing deck details due to new match logged for this deck.");
                loadDeckDetails(currentDeckId)
                    .catch(err => console.error("[deck-details.js] Error reloading deck details after match log:", err));
            }
        }
    });
});