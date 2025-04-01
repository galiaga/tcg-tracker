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

        console.log("deck = ", deck);
        const escapedDeckName = deck.name.replace(/"/g, '&quot;');

        container.innerHTML = `
            <div class="flex items-center justify-between mb-1">
                <h2 id="deck-detail-name" class="text-xl font-bold min-w-0 break-words pr-2">${deck.name}</h2>
                <div class="relative deck-actions">
                    <button type="button" id="deck-detail-options-btn" class="p-1 rounded-full hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-400 flex-shrink-0" data-deck-id="${deck.id}" data-deck-name="${escapedDeckName}" aria-label="Deck options">
                         <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-6 h-6 text-gray-600 pointer-events-none">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M12 6.75a.75.75 0 1 1 0-1.5.75.75 0 0 1 0 1.5ZM12 12.75a.75.75 0 1 1 0-1.5.75.75 0 0 1 0 1.5ZM12 18.75a.75.75 0 1 1 0-1.5.75.75 0 0 1 0 1.5Z" />
                         </svg>
                    </button>
                     <div id="deck-detail-action-menu" class="action-menu hidden absolute right-0 mt-1 w-48 bg-white rounded-md shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none z-20" role="menu" aria-orientation="vertical">
                        <div class="py-1" role="none">
                            <button type="button" class="menu-rename-btn text-gray-700 block w-full px-4 py-2 text-sm text-left hover:bg-gray-100" role="menuitem" data-deck-id="${deck.id}" data-current-name="${escapedDeckName}">
                                Update Name
                            </button>
                            <button type="button" class="menu-delete-btn text-red-600 block w-full px-4 py-2 text-sm text-left hover:bg-gray-100" role="menuitem" data-deck-id="${deck.id}" data-deck-name="${escapedDeckName}">
                                Delete Deck
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            <div class="text-sm text-gray-600 mt-4 space-y-1 border-t pt-4">
                <p><span class="font-semibold text-gray-700">Format:</span> ${deck.deck_type.name}</p>
                <p><span class="font-semibold text-gray-700">Winrate:</span> ${deck.win_rate ?? 0}%</p>
                <p><span class="font-semibold text-gray-700">Matches:</span> ${deck.total_matches ?? 0}</p>
                <p><span class="font-semibold text-gray-700">Wins:</span> ${deck.total_wins ?? 0}</p>
                ${deck.commander_name ? `<p><span class="font-semibold text-gray-700">Commander:</span> ${deck.commander_name}</p>` : ""}
                ${deck.associated_commander_name ? `<p><span class="font-semibold text-gray-700">Associated Commander:</span> ${deck.associated_commander_name}</p>` : ""}
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
             // TODO: Hide loading indicator
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
            // TODO: Hide loading indicator
        }
    }
}

function showFlashMessage(message, category) {
    console.log(`FLASH [${category}]: ${message}`);
    // Implement your actual flash message display logic here
}