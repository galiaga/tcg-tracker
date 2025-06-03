// backend/static/js/ui/decks/deck-details.js
import { authFetch } from '../../auth/auth.js';
import { openQuickAddTagModal, closeQuickAddTagModal } from '../tag-utils.js'; // For deck tags
import { loadDeckMatches } from '../matches/deck-matches.js'; // For recent matches
import { openLogMatchModal } from '../matches/log-match-modal.js'; // For quick log buttons

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

// --- UI Updates & Page Listeners ---
function updatePageTitle(newTitle) {
    document.title = `TCG Tracker: ${newTitle}`;
    const pageTitleElement = document.getElementById("deck-page-title");
    if (pageTitleElement) {
        pageTitleElement.textContent = newTitle || "Deck Details";
    }
}

function setupQuickLogButtonsListener() {
    const container = document.getElementById("deck-details");
    if (!container || container.dataset.quickLogListenerAttached === 'true') return;

    container.addEventListener('click', async (event) => {
        const button = event.target.closest('.quick-log-btn');
        if (!button || button.disabled) return;

        const resultValue = button.dataset.result;
        const deckId = container.dataset.deckId;
        const deckName = container.dataset.deckName || "Selected Deck";

        if (!deckId || typeof resultValue === 'undefined') {
            console.error("Deck ID or result value missing for quick log action.");
            return;
        }

        if (typeof openLogMatchModal === 'function') {
            openLogMatchModal({
                id: deckId,
                name: deckName,
                result: resultValue
            });
        } else {
            console.error("openLogMatchModal function is not available.");
            if (typeof showFlashMessage === 'function') {
                showFlashMessage("Log match feature currently unavailable.", "danger");
            }
        }
    });
    container.dataset.quickLogListenerAttached = 'true';
}

// --- Rendering Deck Details ---
function renderDeckDetails(deck, container) {
    const escapedDeckName = deck.name ? deck.name.replace(/"/g, '"') : "Unnamed Deck";
    let tagPillsHtml = deck.tags?.map(tag =>
        `<span class="tag-pill inline-flex items-center gap-1 bg-violet-100 dark:bg-violet-900 text-violet-800 dark:text-violet-200 text-xs font-medium px-2 py-0.5 rounded-full mr-1 mb-1" data-tag-id="${tag.id}">
            ${tag.name}
            <button type="button" class="remove-tag-button ml-0.5 text-violet-600 dark:text-violet-400 hover:text-violet-800 dark:hover:text-violet-200 font-bold focus:outline-none" aria-label="Remove tag ${tag.name}">×</button>
        </span>`
    ).join('') || '';
    const addTagButtonHtml = `<button type="button" class="add-deck-tag-button inline-flex items-center text-xs font-medium px-2 py-0.5 rounded-md border border-dashed border-gray-400 dark:border-gray-500 text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 hover:text-gray-700 dark:hover:text-gray-300 hover:border-solid hover:border-gray-500 dark:hover:border-gray-400 mb-1" aria-label="Add tag to deck ${deck.name}" data-deck-id="${deck.id}">+ Tag</button>`;
    const tagsContainerHtml = `<div class="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700 px-4 sm:px-6"><h3 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">Tags:</h3><div class="flex flex-wrap items-center gap-x-1">${tagPillsHtml}${addTagButtonHtml}</div></div>`;

    let winrateColorClass = 'text-gray-900 dark:text-gray-100';
    const winRate = deck.win_rate ?? 0;
    if (winRate > 55) winrateColorClass = 'text-green-600 dark:text-green-400 font-semibold';
    else if (winRate >= 45 && winRate <= 55) winrateColorClass = 'text-yellow-600 dark:text-yellow-400 font-semibold';
    else if (winRate > 0 && winRate < 45) winrateColorClass = 'text-red-600 dark:text-red-400 font-semibold';

    const formatDisplay = deck.deck_type?.name || "Commander/EDH"; // Use actual if available, else default

    const statsHtml = `<div class="text-sm space-y-3 mb-4 px-4 sm:px-6">
        <div class="space-y-1">
            <div><span class="font-medium text-gray-500 dark:text-gray-400 mr-1 w-24 inline-block">Format:</span><span class="text-gray-900 dark:text-gray-100">${formatDisplay}</span></div>
            ${deck.commander_name ? `<div><span class="font-medium text-gray-500 dark:text-gray-400 mr-1 w-24 inline-block">Commander:</span><span class="text-gray-900 dark:text-gray-100">${deck.commander_name}</span></div>` : ""}
            ${deck.associated_commander_name ? `<div><span class="font-medium text-gray-500 dark:text-gray-400 mr-1 w-24 inline-block">Associated:</span><span class="text-gray-900 dark:text-gray-100">${deck.associated_commander_name}</span></div>` : ""}
        </div>
        <div class="border-t border-gray-200 dark:border-gray-700 pt-3 space-y-2">
            <div class="flex items-center justify-between gap-x-4">
                <div><span class="font-medium text-gray-500 dark:text-gray-400 mr-1">Winrate:</span><span class="${winrateColorClass} text-base">${winRate}%</span></div>
                <div class="text-right flex gap-x-3">
                    <div><span class="font-medium text-gray-500 dark:text-gray-400 block text-xs">Matches</span><span class="text-gray-900 dark:text-gray-100 block text-base font-medium">${deck.total_matches ?? 0}</span></div>
                    <div><span class="font-medium text-gray-500 dark:text-gray-400 block text-xs">Wins</span><span class="text-gray-900 dark:text-gray-100 block text-base font-medium">${deck.total_wins ?? 0}</span></div>
                </div>
            </div>
        </div>
    </div>`;
    const actionMenuHtml = `<div class="relative deck-actions flex-shrink-0"><button type="button" id="deck-detail-options-btn" class="p-2 rounded-full text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 hover:text-gray-700 dark:hover:text-gray-300 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-violet-500" data-deck-id="${deck.id}" data-deck-name="${escapedDeckName}" aria-label="Deck options" aria-haspopup="true" aria-expanded="false"><svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5 sm:w-6 sm:h-6 pointer-events-none"><path stroke-linecap="round" stroke-linejoin="round" d="M12 6.75a.75.75 0 1 1 0-1.5.75.75 0 0 1 0 1.5ZM12 12.75a.75.75 0 1 1 0-1.5.75.75 0 0 1 0 1.5ZM12 18.75a.75.75 0 1 1 0-1.5.75.75 0 0 1 0 1.5Z" /></svg></button><div id="deck-detail-action-menu" class="action-menu hidden absolute right-0 mt-2 w-48 origin-top-right bg-white dark:bg-gray-800 rounded-md shadow-lg ring-1 ring-black dark:ring-gray-700 ring-opacity-5 focus:outline-none z-20" role="menu" aria-orientation="vertical"><div class="py-1" role="none"><button type="button" class="menu-rename-btn text-gray-700 dark:text-gray-200 group flex items-center w-full px-4 py-2 text-sm text-left hover:bg-gray-100 dark:hover:bg-gray-700 hover:text-gray-900 dark:hover:text-gray-50" role="menuitem" data-deck-id="${deck.id}" data-current-name="${escapedDeckName}"><svg class="mr-3 h-5 w-5 text-gray-400 dark:text-gray-500 group-hover:text-gray-500 dark:group-hover:text-gray-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z" /></svg>Update Name</button><button type="button" class="menu-delete-btn text-red-600 dark:text-red-400 group flex items-center w-full px-4 py-2 text-sm text-left hover:bg-red-50 dark:hover:bg-red-700 hover:text-red-700 dark:hover:text-red-300" role="menuitem" data-deck-id="${deck.id}" data-deck-name="${escapedDeckName}"><svg class="mr-3 h-5 w-5 text-red-400 dark:text-red-500 group-hover:text-red-500 dark:group-hover:text-red-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd" /></svg>Delete Deck</button></div></div></div>`;
    const quickLogButtonsHtml = `<div class="px-4 sm:px-6 mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
        <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2 text-center">Quick Log Result:</h3>
        <div class="flex justify-center space-x-3">
            <button type="button" data-result="0" class="quick-log-btn bg-green-500 hover:bg-green-600 text-white font-medium py-2 px-5 rounded-lg shadow-sm transition flex-1 max-w-[100px]">Win</button>
            <button type="button" data-result="1" class="quick-log-btn bg-red-500 hover:bg-red-600 text-white font-medium py-2 px-5 rounded-lg shadow-sm transition flex-1 max-w-[100px]">Loss</button>
            <button type="button" data-result="2" class="quick-log-btn bg-yellow-500 hover:bg-yellow-600 text-white font-medium py-2 px-5 rounded-lg shadow-sm transition flex-1 max-w-[100px]">Draw</button>
        </div>
    </div>`;

    const matchHistoryContainerId = `deck-${deck.id}-match-history`; // Unique ID for the match history container

    container.innerHTML = `<div class="bg-white dark:bg-gray-800 shadow-lg sm:rounded-lg overflow-hidden">
        <div class="flex items-start justify-between px-4 sm:px-6 pt-4 sm:pt-6 pb-4 mb-2 border-b border-gray-200 dark:border-gray-700">
            <h2 id="deck-detail-name" class="text-xl sm:text-2xl font-semibold text-gray-900 dark:text-gray-100 min-w-0 break-words pr-3">${deck.name}</h2>
            ${actionMenuHtml}
        </div>
        ${statsHtml}
        ${quickLogButtonsHtml}
        ${tagsContainerHtml}
        <div class="mt-6 border-t border-gray-200 dark:border-gray-700">
            <h3 class="px-4 sm:px-6 pt-4 text-lg leading-6 font-medium text-gray-900 dark:text-gray-100">Recent Matches</h3>
            <div id="${matchHistoryContainerId}" class="px-4 sm:px-6 py-4 text-sm text-gray-500 dark:text-gray-400">
                Loading recent matches...
            </div>
        </div>
    </div>`;

    setupActionMenuListeners(deck);
    setupTagActionListeners(deck.id);

    if (typeof loadDeckMatches === 'function') {
        loadDeckMatches(deck.id, matchHistoryContainerId, 5);
    }
}

// --- Tag Handling for Deck ---
async function handleTagClickEvents(event) {
    const removeButton = event.target.closest('.remove-tag-button');
    const addButton = event.target.closest('.add-deck-tag-button');
    const container = document.getElementById("deck-details"); // Main card container
    const deckId = container?.dataset.deckId;

    if (!deckId) return;

    if (removeButton) {
        event.preventDefault(); event.stopPropagation();
        const tagPill = removeButton.closest('.tag-pill');
        const tagId = tagPill?.dataset.tagId;
        if (!tagId) return;

        removeButton.disabled = true;
        if (tagPill) tagPill.style.opacity = '0.5';

        try {
            const csrfToken = await getCsrfToken();
            const response = await authFetch(`/api/decks/${deckId}/tags/${tagId}`, {
                method: 'DELETE',
                headers: { 'X-CSRF-TOKEN': csrfToken }
            });
            if (!response) throw new Error("Auth/Network Error during tag removal.");
            if (response.ok) {
                loadDeckDetails(deckId); // Reload to reflect changes
            } else {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error || `Failed to remove tag (${response.status})`);
            }
        } catch (error) {
            console.error("Error removing tag from deck:", error);
            if (typeof showFlashMessage === 'function') showFlashMessage(error.message || "Could not remove tag.", "danger");
            if (document.body.contains(removeButton)) removeButton.disabled = false;
            if (document.body.contains(tagPill)) tagPill.style.opacity = '1';
        }
    } else if (addButton) {
        event.preventDefault(); event.stopPropagation();
        if (typeof openQuickAddTagModal === 'function') {
            openQuickAddTagModal(deckId, 'deck', () => loadDeckDetails(deckId));
        } else {
            console.error("openQuickAddTagModal function not available.");
        }
    }
}

function setupTagActionListeners(deckId) {
    const container = document.getElementById("deck-details");
    if (!container || container.dataset.tagListenerAttached === 'true') return;
    container.addEventListener('click', handleTagClickEvents);
    container.dataset.tagListenerAttached = 'true';
}

// --- Data Loading ---
async function loadDeckDetails(deckId) {
    const container = document.getElementById("deck-details");
    if (!container) {
        console.error("Deck details container #deck-details not found.");
        return;
    }
    container.innerHTML = `<div class="p-8 text-center text-gray-500 dark:text-gray-400"><svg class="animate-spin h-8 w-8 text-violet-500 dark:text-violet-400 mx-auto mb-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>Loading deck details...</div>`;
    container.removeAttribute('data-tag-listener-attached');
    container.removeAttribute('data-quick-log-listener-attached');
    container.removeAttribute('data-action-menu-listener-attached'); // For action menu

    try {
        const response = await authFetch(`/api/decks/${deckId}`);
        if (!response) throw new Error("Auth/Network Error fetching deck details.");
        if (!response.ok) {
            if (response.status === 404) throw new Error("Deck not found.");
            else {
                const errorData = await response.json().catch(() => ({ message: `Error loading deck details (${response.status})` }));
                throw new Error(errorData.error || errorData.message || `HTTP error ${response.status}`);
            }
        }
        const deck = await response.json();
        if (!deck || typeof deck !== 'object' || deck === null) {
             throw new Error("Received invalid or empty deck data from API.");
        }

        container.dataset.deckId = deck.id;
        container.dataset.deckName = deck.name;

        renderDeckDetails(deck, container); // This renders the card and calls loadDeckMatches
        updatePageTitle(deck.name);
        setupQuickLogButtonsListener(); // Re-attach after render

    } catch(error) {
        console.error("Error fetching or rendering deck details:", error);
        if (typeof showFlashMessage === 'function') showFlashMessage(error.message || "Failed to load deck details.", "danger");
        if (container) {
             container.innerHTML = `<div class="p-6 text-center text-red-500 dark:text-red-400">${error.message || 'Error loading details.'}</div>`;
             delete container.dataset.deckId;
             delete container.dataset.deckName;
         }
        updatePageTitle("Error");
    }
}

// --- Initialization ---
document.addEventListener("DOMContentLoaded", () => {
    const pathParts = window.location.pathname.split("/");
    const idSlug = pathParts[pathParts.length - 1];
    let deckId;

    try {
        const potentialId = idSlug.match(/^(\d+)/);
        if (potentialId && potentialId[1]) {
            deckId = parseInt(potentialId[1], 10);
            if (isNaN(deckId)) throw new Error("Parsed Deck ID is NaN from slug.");
        } else {
            throw new Error("No numeric ID found at the start of the slug.");
        }
    } catch(e) {
         console.error("Invalid Deck ID in URL:", idSlug, e);
         if (typeof showFlashMessage === 'function') showFlashMessage("Invalid Deck ID in URL.", "danger");
         const container = document.getElementById("deck-details");
         if (container) container.innerHTML = '<div class="p-6 text-center text-red-500 dark:text-red-400">Invalid Deck ID in URL.</div>';
         updatePageTitle("Invalid Deck");
         return;
     }

    loadDeckDetails(deckId);

    const quickAddTagModalElement = document.getElementById("quickAddTagModal");
    const quickAddTagModalCloseBtn = document.getElementById("quickAddTagModalCloseButton");
    if (quickAddTagModalElement && quickAddTagModalCloseBtn && typeof closeQuickAddTagModal === 'function') {
        quickAddTagModalCloseBtn.addEventListener('click', closeQuickAddTagModal);
        quickAddTagModalElement.addEventListener('click', (event) => {
            if (event.target === quickAddTagModalElement) closeQuickAddTagModal();
        });
    }

    document.addEventListener('matchLoggedSuccess', (event) => {
        const currentDeckIdOnPage = document.getElementById("deck-details")?.dataset.deckId;
        if (currentDeckIdOnPage) {
            const numericDeckId = parseInt(currentDeckIdOnPage, 10);
            loadDeckDetails(numericDeckId); // This will re-render and re-call loadDeckMatches
        }
    });
});

// --- Action Menu & Deck Actions (Rename, Delete) ---
function setupActionMenuListeners(deck) {
    const container = document.getElementById("deck-details");
    if (!container || container.dataset.actionMenuListenerAttached === 'true') return;

    const optionsBtn = container.querySelector('#deck-detail-options-btn'); // Query within the container
    const actionMenu = container.querySelector('#deck-detail-action-menu');

    if (!optionsBtn || !actionMenu) {
        console.warn("Deck detail action menu buttons not found within #deck-details. Listeners not attached.");
        return;
    }

    const renameBtn = actionMenu.querySelector('.menu-rename-btn');
    const deleteBtn = actionMenu.querySelector('.menu-delete-btn');
    const currentName = deck.name;
    const escapedDeckName = currentName.replace(/"/g, '"');

    optionsBtn.dataset.deckId = deck.id;
    optionsBtn.dataset.deckName = escapedDeckName;
    optionsBtn.setAttribute('aria-label', `Deck options for ${currentName}`);
    if (renameBtn) { renameBtn.dataset.deckId = deck.id; renameBtn.dataset.currentName = escapedDeckName; }
    if (deleteBtn) { deleteBtn.dataset.deckId = deck.id; deleteBtn.dataset.deckName = escapedDeckName; }

    function closeMenu() {
        actionMenu.classList.add('hidden');
        optionsBtn.setAttribute('aria-expanded', 'false');
    }

    optionsBtn.addEventListener('click', (event) => {
        event.stopPropagation();
        const isHidden = actionMenu.classList.toggle('hidden');
        optionsBtn.setAttribute('aria-expanded', String(!isHidden));
    });

    if (renameBtn) {
        renameBtn.addEventListener('click', () => {
            closeMenu();
            promptForRename(renameBtn.dataset.deckId, renameBtn.dataset.currentName);
        });
    }
    if (deleteBtn) {
        deleteBtn.addEventListener('click', () => {
            closeMenu();
            showDeleteConfirmation(deleteBtn.dataset.deckId, deleteBtn.dataset.deckName);
        });
    }
    
    // Use a more specific way to manage click outside listener to avoid conflicts
    const clickOutsideHandler = (event) => {
        if (!actionMenu.classList.contains('hidden') && !optionsBtn.contains(event.target) && !actionMenu.contains(event.target)) {
            closeMenu();
        }
    };
    // Store on a unique property of the button to remove it later if needed, or manage by flag
    if (!optionsBtn.dataset.clickOutsideAttached) {
        document.addEventListener('click', clickOutsideHandler);
        optionsBtn.dataset.clickOutsideAttached = 'true'; // Mark that listener is attached
    }
    // Note: Proper cleanup of this document listener would be needed if the optionsBtn is removed/recreated often.
    // For now, this re-attaches if the flag isn't set.

    container.dataset.actionMenuListenerAttached = 'true';
}

async function updateDeckNameOnServer(deckId, newName) {
    try {
        const csrfToken = await getCsrfToken();
        const response = await authFetch(`/api/decks/${deckId}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json', 'X-CSRF-TOKEN': csrfToken },
            body: JSON.stringify({ deck_name: newName })
        });
        if (response.ok) {
            loadDeckDetails(deckId);
            if (typeof showFlashMessage === 'function') showFlashMessage("Deck renamed successfully!", "success");
        } else {
            const errorData = await response.json().catch(() => ({}));
            if (typeof showFlashMessage === 'function') showFlashMessage(`Error renaming deck: ${errorData.error || response.statusText}`, "danger");
        }
    } catch (error) {
        if (typeof showFlashMessage === 'function') showFlashMessage('Network error. Please try again.', "danger");
    }
}

function promptForRename(deckId, currentName) {
    const unescapedCurrentName = currentName.replace(/"/g, '"');
    const newName = window.prompt(`Enter new name for "${unescapedCurrentName}":`, unescapedCurrentName);
    if (newName && newName.trim() !== '' && newName.trim() !== unescapedCurrentName) {
         updateDeckNameOnServer(deckId, newName.trim());
    } else if (newName !== null && newName.trim() === unescapedCurrentName) {
        // No change
    } else if (newName !== null) {
         if (typeof showFlashMessage === 'function') showFlashMessage("Invalid name provided. Name cannot be empty.", "warning");
    }
}

function showDeleteConfirmation(deckId, deckName) {
    const unescapedDeckName = deckName.replace(/"/g, '"');
     if (window.confirm(`Are you sure you want to delete the deck "${unescapedDeckName}"? This action cannot be undone.`)) {
        deleteDeckOnServer(deckId);
    }
}

async function deleteDeckOnServer(deckId) {
    try {
        const csrfToken = await getCsrfToken();
        if (!csrfToken) {
            if (typeof showFlashMessage === 'function') showFlashMessage("Security token missing. Please refresh.", "danger");
            return;
        }
        const response = await authFetch(`/api/decks/${deckId}`, {
            method: 'DELETE',
            headers: { 'X-CSRF-TOKEN': csrfToken }
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

// --- Fallback Flash Message ---
if (typeof showFlashMessage === 'undefined') {
     function showFlashMessage(message, category) {
          console.log(`FLASH [${category.toUpperCase()}]: ${message}`);
     }
}