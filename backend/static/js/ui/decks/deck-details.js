import { authFetch } from '../../auth/auth.js';
import { openQuickAddTagModal, closeQuickAddTagModal } from '../tagUtils.js';

function updatePageTitle(newTitle) { document.title = `TCG Tracker: ${newTitle}`; }

function renderDeckDetails(deck, container) {
    const escapedDeckName = deck.name.replace(/"/g, '&quot;');
    let tagPillsHtml = '';
    if (deck.tags && deck.tags.length > 0) {
        tagPillsHtml = deck.tags.map(tag =>
            `<span class="tag-pill inline-flex items-center gap-1 bg-blue-100 text-blue-800 text-xs font-medium px-2 py-0.5 rounded-md mr-1 mb-1" data-tag-id="${tag.id}">
                ${tag.name}
                <button type="button" class="remove-tag-button ml-0.5 text-blue-500 hover:text-blue-700 font-bold focus:outline-none" aria-label="Remove tag ${tag.name}">&times;</button>
            </span>`
        ).join('');
    }
    const addTagButtonHtml = `<button type="button" class="add-deck-tag-button inline-flex items-center text-xs font-medium px-2 py-0.5 rounded border border-dashed border-gray-400 text-gray-500 hover:bg-gray-100 hover:text-gray-700 hover:border-solid mb-1" aria-label="Add tag to deck ${deck.name}" data-deck-id="${deck.id}">+ Tag</button>`;
    
    const tagsContainerHtml = `
        <div class="mt-4 pt-4 border-t border-gray-100 px-4 sm:px-6">
             <h3 class="text-sm font-medium text-gray-500 mb-2">Tags:</h3>
             <div class="flex flex-wrap items-center gap-x-1">
                 ${tagPillsHtml}${addTagButtonHtml}
             </div>
        </div>`;

    let winrateColorClass = 'text-gray-900';
    const winRate = deck.win_rate ?? 0;

    if (winRate > 55) {
        winrateColorClass = 'text-green-600 font-semibold';
    } else if (winRate >= 45) {
        winrateColorClass = 'text-yellow-600 font-semibold';
    } else if (winRate > 0) {
        winrateColorClass = 'text-red-600 font-semibold';
    }

    const statsHtml = `
      <div class="text-sm space-y-3 mb-4 px-4 sm:px-6">
        <div class="space-y-1">
          <div>
            <span class="font-medium text-gray-500 mr-1 w-20 inline-block">Format:</span>
            <span class="text-gray-900">${deck.deck_type?.name ?? 'N/A'}</span>
          </div>
          ${deck.commander_name ? `
          <div>
            <span class="font-medium text-gray-500 mr-1 w-20 inline-block">Commander:</span>
            <span class="text-gray-900">${deck.commander_name}</span>
          </div>` : ""}
          ${deck.associated_commander_name ? `
          <div>
            <span class="font-medium text-gray-500 mr-1 w-20 inline-block">Associated:</span>
            <span class="text-gray-900">${deck.associated_commander_name}</span>
          </div>` : ""}
        </div>

        <div class="border-t border-gray-100 pt-3 space-y-2">
            <div class="flex items-center justify-between gap-x-4">
                <div>
                    <span class="font-medium text-gray-500 mr-1">Winrate:</span>
                    <span class="${winrateColorClass} text-base">${winRate}%</span>
                </div>
                <div class="text-right flex gap-x-3">
                     <div>
                        <span class="font-medium text-gray-500 block text-xs">Matches</span>
                        <span class="text-gray-900 block text-base font-medium">${deck.total_matches ?? 0}</span>
                    </div>
                    <div>
                         <span class="font-medium text-gray-500 block text-xs">Wins</span>
                         <span class="text-gray-900 block text-base font-medium">${deck.total_wins ?? 0}</span>
                    </div>
                </div>
            </div>
        </div>
      </div>
    `;

    const actionMenuHtml = `
        <div class="relative deck-actions flex-shrink-0">
            <button type="button" id="deck-detail-options-btn" class="p-2 rounded-full text-gray-500 hover:bg-gray-100 hover:text-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500" data-deck-id="${deck.id}" data-deck-name="${escapedDeckName}" aria-label="Deck options" aria-haspopup="true" aria-expanded="false">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5 sm:w-6 sm:h-6 pointer-events-none"><path stroke-linecap="round" stroke-linejoin="round" d="M12 6.75a.75.75 0 1 1 0-1.5.75.75 0 0 1 0 1.5ZM12 12.75a.75.75 0 1 1 0-1.5.75.75 0 0 1 0 1.5ZM12 18.75a.75.75 0 1 1 0-1.5.75.75 0 0 1 0 1.5Z" /></svg>
            </button>
            <div id="deck-detail-action-menu" class="action-menu hidden absolute right-0 mt-2 w-48 origin-top-right bg-white rounded-md shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none z-20" role="menu" aria-orientation="vertical">
                <div class="py-1" role="none">
                    <button type="button" class="menu-rename-btn text-gray-700 group flex items-center w-full px-4 py-2 text-sm text-left hover:bg-gray-100 hover:text-gray-900" role="menuitem" data-deck-id="${deck.id}" data-current-name="${escapedDeckName}">
                        <svg class="mr-3 h-5 w-5 text-gray-400 group-hover:text-gray-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z" /></svg>Update Name
                    </button>
                    <button type="button" class="menu-delete-btn text-red-600 group flex items-center w-full px-4 py-2 text-sm text-left hover:bg-red-50 hover:text-red-700" role="menuitem" data-deck-id="${deck.id}" data-deck-name="${escapedDeckName}">
                        <svg class="mr-3 h-5 w-5 text-red-400 group-hover:text-red-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd" /></svg>Delete Deck
                    </button>
                </div>
            </div>
        </div>`;

    container.innerHTML = `
        <div class="pb-4">
            <div class="flex items-start justify-between pb-4 mb-4 border-b border-gray-200 px-4 sm:px-6 pt-4 sm:pt-6">
                <h2 id="deck-detail-name" class="text-xl sm:text-2xl font-semibold text-gray-900 min-w-0 break-words pr-3">${deck.name}</h2>
                ${actionMenuHtml}
            </div>
            ${statsHtml}
            ${tagsContainerHtml}
        </div>
        `;

    setupActionMenuListeners(deck);
    setupTagActionListeners(deck.id);
}


let isTagListenerAttached = false;

async function handleTagClickEvents(event) {
    const removeButton = event.target.closest('.remove-tag-button');
    const addButton = event.target.closest('.add-deck-tag-button');
    const container = document.getElementById("deck-details");
    const deckId = container?.querySelector('[data-deck-id]')?.dataset.deckId;

    if (!deckId) return;

    if (removeButton) {
        event.preventDefault();
        event.stopPropagation();
        const tagPill = removeButton.closest('.tag-pill');
        const tagId = tagPill?.dataset.tagId;
        if (!tagId) return;
        removeButton.disabled = true;
        tagPill.style.opacity = '0.5';
        try {
            const response = await authFetch(`/api/decks/${deckId}/tags/${tagId}`, { method: 'DELETE' });
            if (!response) throw new Error("Auth/Network Error");
            if (response.ok) {
                tagPill.remove();
                loadDeckDetails(deckId);
            } else {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error || `Failed to remove tag (${response.status})`);
            }
        } catch (error) {
            console.error("Error removing tag:", error);
            if (typeof showFlashMessage === 'function') showFlashMessage(error.message || "Could not remove tag.", "danger");
            removeButton.disabled = false;
            if(tagPill) tagPill.style.opacity = '1';
        }
    } else if (addButton) {
        event.preventDefault();
        event.stopPropagation();
        if (typeof openQuickAddTagModal === 'function') {
            openQuickAddTagModal(deckId, 'deck', () => loadDeckDetails(deckId));
        } else {
            console.error("openQuickAddTagModal function not available.");
        }
    }
}

function setupTagActionListeners(deckId) {
    const container = document.getElementById("deck-details");
    if (!container || isTagListenerAttached) return;

    container.addEventListener('click', handleTagClickEvents);
    isTagListenerAttached = true;
}

async function loadDeckDetails(deckId) {
    const container = document.getElementById("deck-details");
    if (!container) return;
    container.innerHTML = `<div class="p-6 text-center text-gray-500">Loading deck details...</div>`;
    isTagListenerAttached = false;

    try {
        const response = await authFetch(`/api/decks/${deckId}`);
        if (!response) throw new Error("Auth/Network Error");
        if (!response.ok) {
            if (response.status === 404) throw new Error("Deck not found.");
            else throw new Error(`Error loading deck details (${response.status})`);
        }
        const deck = await response.json();
        if (!deck) {
             throw new Error("Received empty deck data from API.");
        }
        renderDeckDetails(deck, container);
        updatePageTitle(deck.name);
    } catch(error) {
        console.error("Error fetching or rendering deck details:", error);
        if (typeof showFlashMessage === 'function') showFlashMessage(error.message, "danger");
        if (container) container.innerHTML = `<div class="p-6 text-center text-red-500">${error.message || 'Error loading details.'}</div>`;
        updatePageTitle("Error");
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const pathParts = window.location.pathname.split("/");
    const idSlug = pathParts[pathParts.length - 1];
    const deckId = parseInt(idSlug.split("-")[0]);

    if (isNaN(deckId)) {
        console.error("Invalid Deck ID in URL");
        if (typeof showFlashMessage === 'function') showFlashMessage("Invalid Deck ID.", "danger");
        const container = document.getElementById("deck-details");
        if (container) container.innerHTML = '<div class="p-6 text-center text-red-500">Invalid Deck ID in URL.</div>';
        return;
    }

    loadDeckDetails(deckId);

    const quickAddModal = document.getElementById("quickAddTagModal");
    const quickAddModalCloseBtn = document.getElementById("quickAddModalCloseButton");
    if (quickAddModal && quickAddModalCloseBtn && typeof closeQuickAddTagModal === 'function') {
        quickAddModalCloseBtn.addEventListener('click', closeQuickAddTagModal);
        quickAddModal.addEventListener('click', (event) => {
            if (event.target === quickAddModal) {
                 closeQuickAddTagModal();
            }
        });
    }
});

function setupActionMenuListeners(deck) {
    const optionsBtn = document.getElementById('deck-detail-options-btn');
    const actionMenu = document.getElementById('deck-detail-action-menu');
    if (!optionsBtn || !actionMenu) return;
    const renameBtn = actionMenu.querySelector('.menu-rename-btn');
    const deleteBtn = actionMenu.querySelector('.menu-delete-btn');
    
    let currentName = deck.name; 

    optionsBtn.dataset.deckName = deck.name.replace(/"/g, '&quot;');

    function closeMenu() { actionMenu.classList.add('hidden'); }

    optionsBtn.addEventListener('click', (event) => {
        event.stopPropagation();
        actionMenu.classList.toggle('hidden');
    });
    if (renameBtn) {
        renameBtn.dataset.currentName = currentName.replace(/"/g, '&quot;'); 
        renameBtn.addEventListener('click', () => {
            closeMenu();
            promptForRename(deck.id, currentName);
        });
    }
    if (deleteBtn) {
        deleteBtn.dataset.deckName = currentName.replace(/"/g, '&quot;'); 
        deleteBtn.addEventListener('click', () => {
            closeMenu();
            showDeleteConfirmation(deck.id, currentName);
        });
    }
    document.addEventListener('click', (event) => {
        if (!optionsBtn.contains(event.target) && !actionMenu.contains(event.target)) {
            if (!actionMenu.classList.contains('hidden')) { closeMenu(); }
        }
    });

    function promptForRename(deckId, name) {
        const newName = window.prompt(`Enter new name for "${name}":`, name);
        if (newName && newName.trim() !== '' && newName !== name) {
             updateDeckNameOnServer(deckId, newName.trim());
        } else if (newName !== null && newName !== name) {
             alert("Invalid name provided.");
        }
    }

    async function updateDeckNameOnServer(deckId, newName) {
        try {
            const response = await authFetch(`/api/decks/${deckId}`, {
                method: 'PATCH',
                body: JSON.stringify({ deck_name: newName })
            });
            if (response.ok) {
                const titleElement = document.getElementById('deck-detail-name');
                if (titleElement) titleElement.textContent = newName;
                currentName = newName;

                const updatedEscapedName = newName.replace(/"/g, '&quot;');
                optionsBtn.dataset.deckName = updatedEscapedName;
                optionsBtn.ariaLabel = `Deck options for ${newName}`;
                if (renameBtn) renameBtn.dataset.currentName = updatedEscapedName;
                if (deleteBtn) deleteBtn.dataset.deckName = updatedEscapedName;

                if (typeof showFlashMessage === 'function') showFlashMessage("Deck renamed successfully!", "success");
                updatePageTitle(newName);
            } else {
                const errorData = await response.json().catch(() => ({}));
                console.error(`Failed to rename deck ${deckId}. Status: ${response.status}`, errorData);
                if (typeof showFlashMessage === 'function') showFlashMessage(`Error renaming deck: ${errorData.error || response.statusText}`, "danger");
            }
        } catch (error) {
            console.error('Network error while renaming deck:', error);
            if (typeof showFlashMessage === 'function') showFlashMessage('Network error. Please try again.', "danger");
        }
    }

    function showDeleteConfirmation(deckId, deckName) {
         if (window.confirm(`Are you sure you want to permanently delete the deck "${deckName}"? This cannot be undone.`)) {
            deleteDeckOnServer(deckId);
        }
    }

    async function deleteDeckOnServer(deckId) {
        try {
            const response = await authFetch(`/api/decks/${deckId}`, { method: 'DELETE' });
            if (response.ok) {
                if (typeof showFlashMessage === 'function') showFlashMessage("Deck deleted successfully. Redirecting...", "success");
                setTimeout(() => { window.location.href = '/my-decks'; }, 1500);
            } else {
                const errorData = await response.json().catch(() => ({}));
                console.error(`Failed to delete deck ${deckId}. Status: ${response.status}`, errorData);
                if (typeof showFlashMessage === 'function') showFlashMessage(`Error deleting deck: ${errorData.error || response.statusText}`, "danger");
            }
        } catch (error) {
            console.error('Network error while deleting deck:', error);
            if (typeof showFlashMessage === 'function') showFlashMessage('Network error. Please try again.', "danger");
        }
    }
}

if (typeof showFlashMessage === 'undefined') {
     function showFlashMessage(message, category) {
          console.log(`FLASH [${category}]: ${message}`);
     }
}