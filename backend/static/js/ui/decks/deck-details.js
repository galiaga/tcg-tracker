// backend/static/js/ui/decks/deck-details.js

import { authFetch } from '../../auth/auth.js';
import { openQuickAddTagModal, closeQuickAddTagModal, handleRemoveTagClick as handleRemoveDeckTagFromCard } from '../tag-utils.js';
import { loadDeckMatches } from '../matches/deck-matches.js';
import { openLogMatchModal } from '../matches/log-match-modal.js';

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
    document.title = `TCG Tracker: ${newTitle || 'Deck Details'}`;
    const pageTitleElement = document.getElementById("deck-page-title");
    if (pageTitleElement) {
        pageTitleElement.textContent = newTitle || "Deck Details";
    }
}

function setupQuickLogButtonsListener(deckId, deckName) {
    const container = document.getElementById("deck-details");
    if (!container || container.dataset.quickLogListenerAttached === 'true') return;

    container.addEventListener('click', (event) => {
        const button = event.target.closest('.quick-log-btn');
        if (!button || button.disabled) return;

        const resultValue = button.dataset.result;

        if (!deckId || typeof resultValue === 'undefined') {
            console.error("Deck ID or result value missing for quick log action.");
            return;
        }

        if (typeof openLogMatchModal === 'function') {
            openLogMatchModal({
                id: parseInt(deckId, 10),
                name: deckName,
                result: parseInt(resultValue, 10)
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
    let totalMatches = parseInt(deck.total_matches ?? 0, 10);

    let tagPillsHtml = deck.tags?.map(tag =>
        `<span class="tag-pill inline-flex items-center gap-1 bg-violet-100 dark:bg-violet-700/60 text-violet-800 dark:text-violet-200 text-xs font-semibold px-2.5 py-1 rounded-full mr-1 mb-1" data-tag-id="${tag.id}">
            <span>${tag.name}</span>
            <button type="button" class="remove-tag-button ml-1.5 -mr-0.5 flex-shrink-0 rounded-full p-0.5 text-violet-500 dark:text-violet-400 hover:bg-violet-200 dark:hover:bg-violet-600 focus:outline-none focus:ring-1 focus:ring-violet-400 dark:focus:ring-violet-500" aria-label="Remove tag ${tag.name}">
                <svg class="h-2.5 w-2.5" stroke="currentColor" fill="none" viewBox="0 0 8 8"><path stroke-linecap="round" stroke-width="1.5" d="M1 1l6 6m0-6L1 7" /></svg>
            </button>
        </span>`
    ).join('') || '';

    const addTagButtonHtml = `<button type="button" class="add-deck-tag-button text-xs font-medium text-violet-600 dark:text-violet-400 hover:text-violet-800 dark:hover:text-violet-200 border border-dashed border-violet-400 dark:border-violet-500 rounded-full px-2.5 py-1 hover:bg-violet-100 dark:hover:bg-violet-700/30 transition-colors leading-tight focus:outline-none focus:ring-1 focus:ring-violet-500" aria-label="Add tag to deck ${deck.name}" data-deck-id="${deck.id}">+ Tag</button>`;
    const tagsContainerHtml = `<div class="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700/50 px-4 sm:px-6"><h3 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">Tags:</h3><div class="flex flex-wrap items-center gap-x-1.5 gap-y-1.5">${tagPillsHtml}${addTagButtonHtml}</div></div>`;

    let winrateColorClass = 'text-gray-900 dark:text-gray-100';
    const winRate = parseFloat(deck.win_rate ?? 0);
    if (winRate > 55) {
        winrateColorClass = 'text-green-600 dark:text-green-400 font-semibold';
    } else if (winRate >= 45 && winRate <= 55) {
        winrateColorClass = 'text-yellow-600 dark:text-yellow-400 font-semibold';
    } else if (totalMatches > 0 && winRate < 45) { 
        winrateColorClass = 'text-red-600 dark:text-red-400 font-semibold';
    }

    const formatDisplay = deck.format_name || "Commander";

    const statsHtml = `<div class="text-sm space-y-3 mb-4 px-4 sm:px-6">
        <div class="space-y-1">
            <div><span class="font-medium text-gray-500 dark:text-gray-400 mr-1 w-24 inline-block">Format:</span><span class="text-gray-900 dark:text-gray-100">${formatDisplay}</span></div>
            ${deck.commander_name ? `<div><span class="font-medium text-gray-500 dark:text-gray-400 mr-1 w-24 inline-block">Commander:</span><span class="text-gray-900 dark:text-gray-100">${deck.commander_name}</span></div>` : ""}
            ${deck.associated_commander_name ? `<div><span class="font-medium text-gray-500 dark:text-gray-400 mr-1 w-24 inline-block">Associated:</span><span class="text-gray-900 dark:text-gray-100">${deck.associated_commander_name}</span></div>` : ""}
        </div>
        <div class="border-t border-gray-200 dark:border-gray-700/50 pt-3 space-y-2">
            <div class="flex items-center justify-between gap-x-4">
                <div><span class="font-medium text-gray-500 dark:text-gray-400 mr-1">Winrate:</span><span class="${winrateColorClass} text-base">${winRate.toFixed(2)}%</span></div>
                <div class="text-right flex gap-x-3">
                    <div><span class="font-medium text-gray-500 dark:text-gray-400 block text-xs">Matches</span><span class="text-gray-900 dark:text-gray-100 block text-base font-medium">${totalMatches}</span></div>
                    <div><span class="font-medium text-gray-500 dark:text-gray-400 block text-xs">Wins</span><span class="text-gray-900 dark:text-gray-100 block text-base font-medium">${deck.total_wins ?? 0}</span></div>
                </div>
            </div>
        </div>
    </div>`;
    const actionMenuHtml = `<div class="relative deck-actions flex-shrink-0"><button type="button" id="deck-detail-options-btn" class="p-2 rounded-full text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 hover:text-gray-700 dark:hover:text-gray-300 focus:outline-none focus:ring-2 focus:ring-offset-2 dark:focus:ring-offset-gray-800 focus:ring-violet-500" data-deck-id="${deck.id}" data-deck-name="${escapedDeckName}" aria-label="Deck options" aria-haspopup="true" aria-expanded="false"><svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5 sm:w-6 sm:h-6 pointer-events-none"><path stroke-linecap="round" stroke-linejoin="round" d="M12 6.75a.75.75 0 1 1 0-1.5.75.75 0 0 1 0 1.5ZM12 12.75a.75.75 0 1 1 0-1.5.75.75 0 0 1 0 1.5ZM12 18.75a.75.75 0 1 1 0-1.5.75.75 0 0 1 0 1.5Z" /></svg></button><div id="deck-detail-action-menu" class="action-menu hidden absolute right-0 mt-2 w-48 origin-top-right bg-white dark:bg-gray-800 rounded-md shadow-lg ring-1 ring-black dark:ring-gray-700 ring-opacity-5 focus:outline-none z-20" role="menu" aria-orientation="vertical"><div class="py-1" role="none"><button type="button" class="menu-rename-btn text-gray-700 dark:text-gray-200 group flex items-center w-full px-4 py-2 text-sm text-left hover:bg-gray-100 dark:hover:bg-gray-700 hover:text-gray-900 dark:hover:text-gray-50" role="menuitem" data-deck-id="${deck.id}" data-current-name="${escapedDeckName}"><svg class="mr-3 h-5 w-5 text-gray-400 dark:text-gray-500 group-hover:text-gray-500 dark:group-hover:text-gray-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z" /></svg>Update Name</button><button type="button" class="menu-delete-btn text-red-600 dark:text-red-400 group flex items-center w-full px-4 py-2 text-sm text-left hover:bg-red-50 dark:hover:bg-red-700 hover:text-red-700 dark:hover:text-red-300" role="menuitem" data-deck-id="${deck.id}" data-deck-name="${escapedDeckName}"><svg class="mr-3 h-5 w-5 text-red-400 dark:text-red-500 group-hover:text-red-500 dark:group-hover:text-red-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd" /></svg>Delete Deck</button></div></div></div>`;
    const quickLogButtonsHtml = `<div class="px-4 sm:px-6 mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
        <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2 text-center">Quick Log Result:</h3>
        <div class="flex justify-center space-x-3">
            <button type="button" data-result="0" class="quick-log-btn bg-green-500 hover:bg-green-600 text-white font-medium py-2 px-5 rounded-lg shadow-sm transition flex-1 max-w-[100px]">Win</button>
            <button type="button" data-result="1" class="quick-log-btn bg-red-500 hover:bg-red-600 text-white font-medium py-2 px-5 rounded-lg shadow-sm transition flex-1 max-w-[100px]">Loss</button>
            <button type="button" data-result="2" class="quick-log-btn bg-yellow-500 hover:bg-yellow-600 text-white font-medium py-2 px-5 rounded-lg shadow-sm transition flex-1 max-w-[100px]">Draw</button>
        </div>
    </div>`;

    const matchHistoryContainerId = `deck-${deck.id}-match-history`;

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
                <p class="text-sm text-gray-500 dark:text-gray-400">Loading recent matches...</p>
            </div>
        </div>
    </div>`;

    // Call these AFTER innerHTML is set to ensure elements exist
    setupActionMenuListeners(deck); 
    setupTagActionListeners(deck.id); // Pass deck.id
    setupQuickLogButtonsListener(deck.id, deck.name); // Pass deck.id and deck.name

    if (typeof loadDeckMatches === 'function') {
        loadDeckMatches(deck.id, matchHistoryContainerId, 5) // Load recent matches
            .catch(err => console.error(`[deck-details.js] Error in loadDeckMatches from renderDeckDetails:`, err));
    }
}

// --- Tag Handling for Deck ---
async function handleTagClickEvents(event) {
    const removeButton = event.target.closest('.remove-tag-button');
    const addButton = event.target.closest('.add-deck-tag-button');
    const container = document.getElementById("deck-details");
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
                loadDeckDetails(deckId); // Reload all deck details to reflect tag changes and stats
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
            openQuickAddTagModal(deckId, 'deck', () => loadDeckDetails(deckId)); // Refresh all details
        } else {
            console.error("openQuickAddTagModal function not available.");
        }
    }
}

function setupTagActionListeners(deckId) { // deckId might not be strictly needed if we always get from container
    const container = document.getElementById("deck-details");
    if (!container) return;
    // More robust listener removal/attachment
    if (container.dataset.tagListenerAttached === 'true') {
        container.removeEventListener('click', handleTagClickEvents);
    }
    container.addEventListener('click', handleTagClickEvents);
    container.dataset.tagListenerAttached = 'true';
}

// --- Data Loading ---
async function loadDeckDetails(deckId) {
    const container = document.getElementById("deck-details");
    if (!container) {
        console.error("[deck-details.js] Deck details container #deck-details not found.");
        return;
    }
    container.innerHTML = `<div class="p-8 text-center text-gray-500 dark:text-gray-400"><svg class="animate-spin h-8 w-8 text-violet-500 dark:text-violet-400 mx-auto mb-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>Loading deck details...</div>`;
    
    // Clear listener flags before re-rendering, as elements they were attached to will be gone
    container.removeAttribute('data-tag-listener-attached');
    container.removeAttribute('data-quick-log-listener-attached');
    container.removeAttribute('data-action-menu-listener-attached');

    try {
        const response = await authFetch(`/api/decks/${deckId}`);
        if (!response) throw new Error("Auth/Network Error fetching deck details.");

        if (!response.ok) {
            if (response.status === 404) throw new Error("Deck not found.");
            const errorData = await response.json().catch(() => ({ message: `Error loading deck details (${response.status})` }));
            throw new Error(errorData.error || errorData.message || `HTTP error ${response.status}`);
        }
        const deck = await response.json();
        if (!deck || typeof deck !== 'object' || deck === null || !deck.id) {
             throw new Error("Received invalid or empty deck data from API.");
        }

        container.dataset.deckId = deck.id; // Store ID on the container
        container.dataset.deckName = deck.name; // Store name for quick log

        renderDeckDetails(deck, container); // This will re-render the content
        updatePageTitle(deck.name);
        // Listeners are now set up inside renderDeckDetails or called from there

    } catch(error) {
        console.error("[deck-details.js] Error in loadDeckDetails:", error);
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
    const deckDetailsContainer = document.getElementById("deck-details");
    if (!deckDetailsContainer) {
        return; 
    }

    const pathParts = window.location.pathname.split("/");
    const idSlug = pathParts[pathParts.length - 1];
    let deckId;

    try {
        const potentialId = idSlug.match(/^(\d+)/);
        if (potentialId && potentialId[1]) {
            deckId = parseInt(potentialId[1], 10);
            if (isNaN(deckId)) throw new Error("Parsed Deck ID is NaN from slug.");
        } else {
            // Fallback to data attribute if set by server-side template
            if (deckDetailsContainer.dataset.deckId) { 
                deckId = parseInt(deckDetailsContainer.dataset.deckId, 10);
                if (isNaN(deckId)) throw new Error("Parsed Deck ID from data attribute is NaN.");
            } else {
                throw new Error("No numeric ID found in URL slug or data attribute.");
            }
        }
    } catch(e) {
         console.error("Invalid Deck ID in URL:", idSlug, e);
         if (typeof showFlashMessage === 'function') showFlashMessage("Invalid Deck ID in URL.", "danger");
         if (deckDetailsContainer) deckDetailsContainer.innerHTML = '<div class="p-6 text-center text-red-500 dark:text-red-400">Invalid Deck ID in URL.</div>';
         updatePageTitle("Invalid Deck");
         return;
     }

    if (deckId) {
        loadDeckDetails(deckId);
    } else {
        console.error("[deck-details.js] Deck ID could not be determined. Cannot load details.");
        if (deckDetailsContainer) deckDetailsContainer.innerHTML = '<div class="p-6 text-center text-red-500 dark:text-red-400">Could not determine Deck ID.</div>';
        updatePageTitle("Error");
        return;
    }

    // Setup listeners for the Quick Add Tag Modal (for adding tags to THIS deck)
    const quickAddTagModalElement = document.getElementById("quickAddTagModal");
    const quickAddTagModalCloseBtn = document.getElementById("quickAddTagModalCloseButton");
    const quickAddTagModalDoneBtn = document.getElementById("quickAddTagModalDoneButton");

    if (quickAddTagModalElement && quickAddTagModalCloseBtn && quickAddTagModalDoneBtn && typeof closeQuickAddTagModal === 'function') {
        quickAddTagModalCloseBtn.addEventListener('click', closeQuickAddTagModal);
        quickAddTagModalDoneBtn.addEventListener('click', closeQuickAddTagModal);
        quickAddTagModalElement.addEventListener('click', (event) => {
            if (event.target === quickAddTagModalElement) closeQuickAddTagModal();
        });
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape' && quickAddTagModalElement && !quickAddTagModalElement.classList.contains('hidden')) {
                closeQuickAddTagModal();
            }
        });
    }

    // Listen for the GLOBAL custom event
    document.addEventListener('globalMatchLoggedSuccess', (event) => {
        const currentDeckIdOnPageString = deckDetailsContainer?.dataset.deckId;
        
        if (currentDeckIdOnPageString && event.detail && typeof event.detail.deckId !== 'undefined') {
            const eventDeckId = parseInt(event.detail.deckId, 10);
            const pageDeckId = parseInt(currentDeckIdOnPageString, 10);

            if (eventDeckId === pageDeckId) {
                loadDeckDetails(pageDeckId) // Reload ALL deck details
                    .catch(err => console.error("[deck-details.js] Error reloading deck details after match log:", err));
            }
        } else if (currentDeckIdOnPageString) { 
            const pageDeckId = parseInt(currentDeckIdOnPageString, 10);
            loadDeckDetails(pageDeckId)
                .catch(err => console.error("[deck-details.js] Error reloading deck details after match log (no event deckId):", err));
        }
    });
});

// --- Action Menu & Deck Actions (Rename, Delete) ---
function setupActionMenuListeners(deck) {
    const container = document.getElementById("deck-details");
    const oldOptionsBtn = container?.querySelector('#deck-detail-options-btn');
    if (oldOptionsBtn && oldOptionsBtn._clickOutsideHandler) {
        document.removeEventListener('click', oldOptionsBtn._clickOutsideHandler);
        delete oldOptionsBtn._clickOutsideHandler;
    }
    container?.removeAttribute('data-action-menu-listener-attached');

    const optionsBtn = container?.querySelector('#deck-detail-options-btn');
    const actionMenu = container?.querySelector('#deck-detail-action-menu');

    if (!optionsBtn || !actionMenu) {
        return;
    }
    // if (container.dataset.actionMenuListenerAttached === 'true') return; // This check might be too aggressive if elements are recreated

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
    
    const clickOutsideHandler = (event) => {
        if (!actionMenu.classList.contains('hidden') && !optionsBtn.contains(event.target) && !actionMenu.contains(event.target)) {
            closeMenu();
        }
    };
    
    optionsBtn._clickOutsideHandler = clickOutsideHandler; 
    document.addEventListener('click', optionsBtn._clickOutsideHandler);

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
     window.showFlashMessage = function showFlashMessage(message, category) {
     }
}