import { authFetch } from './auth/auth.js';

function updatePageTitle(newTitle) {
    document.title = `TCG Tracker: ${newTitle}`;
}

document.addEventListener("DOMContentLoaded", async () => {
    const pathParts = window.location.pathname.split("/");
    const idSlug = pathParts[pathParts.length - 1];
    const deckId = parseInt(idSlug.split("-")[0]);

    if (isNaN(deckId)) {
        console.error("Invalid Deck ID in URL");
        showFlashMessage("Invalid Deck ID.", "danger");
        return;
    }


    try {
        const token = localStorage.getItem("access_token");
        if (!token) {
            showFlashMessage("Authentication required.", "warning");
            return;
        }

        const response = await authFetch(`/api/decks/${deckId}`, { 
            method: "GET",
            headers: {
                "Authorization": `Bearer ${token}`,
                "Content-Type": "application/json"
            }
        });

        if (!response.ok) {
             if (response.status === 404) {
                 showFlashMessage("Deck not found.", "warning");
             } else {
                showFlashMessage(`Error loading deck details (${response.status})`, "danger");
             }
             return;
        }

        const deck = await response.json();
        const container = document.getElementById("deck-details");

        if (!container) {
            console.error("Container element #deck-details not found!");
            return;
        }

        const escapedDeckName = deck.name.replace(/"/g, '&quot;');

        container.innerHTML = `
            <div class="p-4 sm:p-6">
                <div class="flex items-start justify-between pb-4 mb-4 border-b border-gray-200">
                    <h2 id="deck-detail-name" class="text-xl sm:text-2xl font-semibold text-gray-900 min-w-0 break-words pr-3">
                        ${deck.name}
                    </h2>
                    <div class="relative deck-actions flex-shrink-0">
                        <button type="button" id="deck-detail-options-btn" class="p-2 rounded-full text-gray-500 hover:bg-gray-100 hover:text-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500" data-deck-id="${deck.id}" data-deck-name="${escapedDeckName}" aria-label="Deck options" aria-haspopup="true" aria-expanded="false">
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5 sm:w-6 sm:h-6 pointer-events-none">
                                <path stroke-linecap="round" stroke-linejoin="round" d="M12 6.75a.75.75 0 1 1 0-1.5.75.75 0 0 1 0 1.5ZM12 12.75a.75.75 0 1 1 0-1.5.75.75 0 0 1 0 1.5ZM12 18.75a.75.75 0 1 1 0-1.5.75.75 0 0 1 0 1.5Z" />
                            </svg>
                        </button>
                        <div id="deck-detail-action-menu" class="action-menu hidden absolute right-0 mt-2 w-48 origin-top-right bg-white rounded-md shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none z-20" role="menu" aria-orientation="vertical">
                            <div class="py-1" role="none">
                                <button type="button" class="menu-rename-btn text-gray-700 group flex items-center w-full px-4 py-2 text-sm text-left hover:bg-gray-100 hover:text-gray-900" role="menuitem" data-deck-id="${deck.id}" data-current-name="${escapedDeckName}">
                                    <svg class="mr-3 h-5 w-5 text-gray-400 group-hover:text-gray-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"> <path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z" /> </svg>
                                    Update Name
                                </button>
                                <button type="button" class="menu-delete-btn text-red-600 group flex items-center w-full px-4 py-2 text-sm text-left hover:bg-red-50 hover:text-red-700" role="menuitem" data-deck-id="${deck.id}" data-deck-name="${escapedDeckName}">
                                    <svg class="mr-3 h-5 w-5 text-red-400 group-hover:text-red-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"> <path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd" /> </svg>
                                    Delete Deck
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="flex flex-wrap gap-x-4 gap-y-2 text-sm">
                    <span>
                        <span class="font-medium text-gray-500 mr-1">Format:</span>
                        <span class="text-gray-900">${deck.deck_type.name}</span>
                    </span>
                    <span>
                        <span class="font-medium text-gray-500 mr-1">Winrate:</span>
                        <span class="text-gray-900">${deck.win_rate ?? 0}%</span>
                    </span>
                    <span>
                        <span class="font-medium text-gray-500 mr-1">Matches:</span>
                        <span class="text-gray-900">${deck.total_matches ?? 0}</span>
                    </span>
                    <span>
                        <span class="font-medium text-gray-500 mr-1">Wins:</span>
                        <span class="text-gray-900">${deck.total_wins ?? 0}</span>
                    </span>

                    ${deck.commander_name ? `
                    <span>
                        <span class="font-medium text-gray-500 mr-1">Commander:</span>
                        <span class="text-gray-900">${deck.commander_name}</span>
                    </span>
                    ` : ""}

                    ${deck.associated_commander_name ? `
                    <span>
                        <span class="font-medium text-gray-500 mr-1">Associated Commander:</span>
                        <span class="text-gray-900">${deck.associated_commander_name}</span>
                    </span>
                    ` : ""}
                </div>
            </div>
        `;

        setupActionMenuListeners(deck);

        updatePageTitle(deck.name);

    } catch (error) {
        console.error("Error fetching or rendering deck details:", error);
        showFlashMessage(error.message || "An unexpected error occurred", "danger");
    }
});


/**
 * Sets up event listeners for the action menu on the detail page.
 * @param {object} deck - The deck data object
 */
function setupActionMenuListeners(deck) {
    const optionsBtn = document.getElementById('deck-detail-options-btn');
    const actionMenu = document.getElementById('deck-detail-action-menu');

    if (!optionsBtn || !actionMenu) {
        console.error("Could not find options button or menu to attach listeners.");
        return;
    }

    const renameBtn = actionMenu.querySelector('.menu-rename-btn');
    const deleteBtn = actionMenu.querySelector('.menu-delete-btn');
    let currentName = optionsBtn.dataset.deckName;

    function closeMenu() {
        actionMenu.classList.add('hidden');
    }

    optionsBtn.addEventListener('click', (event) => {
        event.stopPropagation();
        actionMenu.classList.toggle('hidden');
    });

    if (renameBtn) {
        renameBtn.addEventListener('click', () => {
            closeMenu();
            promptForRename(deck.id, currentName);
        });
    }

    if (deleteBtn) {
        deleteBtn.addEventListener('click', () => {
            closeMenu();
            showDeleteConfirmation(deck.id, currentName);
        });
    }

    document.addEventListener('click', (event) => {
        if (!optionsBtn.contains(event.target) && !actionMenu.contains(event.target)) {
             if (!actionMenu.classList.contains('hidden')) { 
                 closeMenu();
             }
        }
    });

    function promptForRename(deckId, name) {
        const newName = window.prompt(`Enter new name for "${name}":`, name);
        if (newName && newName.trim() !== '' && newName !== name) {
             updateDeckNameOnServer(deckId, newName.trim());
        } else if (newName !== null) {
            alert("Invalid or unchanged name provided.");
        }
    }

    async function updateDeckNameOnServer(deckId, newName) {
        const token = localStorage.getItem('access_token'); 

        try {
            const response = await authFetch(`/api/decks/${deckId}`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ deck_name: newName })
            });

            if (response.ok) {
                const titleElement = document.getElementById('deck-detail-name');
                if (titleElement) titleElement.textContent = newName;

                currentName = newName;

                optionsBtn.dataset.deckName = newName;
                optionsBtn.ariaLabel = `Deck options for ${newName}`;
                if (renameBtn) renameBtn.dataset.currentName = newName;
                if (deleteBtn) deleteBtn.dataset.deckName = newName;

                showFlashMessage("Deck renamed successfully!", "success");

            } else {
                 const errorData = await response.json().catch(() => ({}));
                 console.error(`Failed to rename deck ${deckId}. Status: ${response.status}`, errorData);
                 showFlashMessage(`Error renaming deck: ${errorData.error || response.statusText}`, "danger");
            }

        } catch (error) {
             console.error('Network error while renaming deck:', error);
             showFlashMessage('Network error. Please try again.', "danger");
        } finally {
          }
    }

    function showDeleteConfirmation(deckId, deckName) {
         if (window.confirm(`Are you sure you want to permanently delete the deck "${deckName}"?`)) {
            deleteDeckOnServer(deckId);
        } else {
            console.log('Deck deletion cancelled.');
        }
    }

    async function deleteDeckOnServer(deckId) {
        console.log(`Attempting to delete deck ${deckId} on server...`);
        const token = localStorage.getItem('access_token');

        try {
            const response = await authFetch(`/api/decks/${deckId}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
            });

             if (response.ok) {
                 console.log(`Deck ${deckId} deleted successfully.`);
                 showFlashMessage("Deck deleted successfully. Redirecting...", "success");
                 setTimeout(() => {
                    window.location.href = '/my-decks';
                 }, 1500);

            } else {
                 const errorData = await response.json().catch(() => ({}));
                 console.error(`Failed to delete deck ${deckId}. Status: ${response.status}`, errorData);
                 showFlashMessage(`Error deleting deck: ${errorData.error || response.statusText}`, "danger");
            }
        } catch (error) {
             console.error('Network error while deleting deck:', error);
             showFlashMessage('Network error. Please try again.', "danger");
        } finally {
        }
    }
}

function showFlashMessage(message, category) {
    console.log(`FLASH [${category}]: ${message}`);
}