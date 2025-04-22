// backend/static/js/ui/matches/match-actions.js

import { authFetch } from '../../auth/auth.js';
// Assuming showFlashMessage might be globally available or imported elsewhere
// import { showFlashMessage } from '../../utils.js';

// --- CSRF Token Retrieval ---
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

// --- Match Deletion API Call ---
async function deleteMatchOnServer(matchId) {
    try {
        const csrfToken = await getCsrfToken();
        if (!csrfToken) return false;

        const response = await authFetch(`/api/matches/${matchId}`, {
            method: 'DELETE',
            headers: { 'X-CSRF-TOKEN': csrfToken }
        });

        if (response.status === 204 || response.ok) {
            return true;
        } else {
            let errorMsg = `Failed to hide match. Status: ${response.status}`;
            try { const errorData = await response.json(); errorMsg += ` - ${errorData.error || 'Unknown server error'}`; } catch (e) { /* Ignore */ }
            console.error(errorMsg);
            if (typeof showFlashMessage === 'function') showFlashMessage(errorMsg, "danger");
            return false;
        }
    } catch (error) {
        console.error('Network or other error during match hiding:', error);
        if (typeof showFlashMessage === 'function') {
            showFlashMessage('An error occurred while hiding the match. Please check connection.', "danger");
        }
        return false;
    }
}

// --- Deletion Confirmation and UI Handling ---
function showDeleteMatchConfirmation(matchId, matchElement, onMatchDeletedCallback) {
    const confirmationMessage = `Are you sure you want to hide this match (ID: ${matchId})? It will be removed from the list but can potentially be recovered later.`;

    if (!window.confirm(confirmationMessage)) return;

    const deleteButton = matchElement.querySelector('.menu-delete-match-btn');
    if (deleteButton) {
        deleteButton.disabled = true;
        deleteButton.innerHTML = `<svg class="animate-spin mr-3 h-5 w-5 text-red-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>Hiding...`;
    }

    deleteMatchOnServer(matchId).then(success => {
        if (success) {
            matchElement.style.transition = 'opacity 0.3s ease-out, max-height 0.3s ease-out, margin 0.3s ease-out, padding 0.3s ease-out, border-width 0.3s ease-out';
            matchElement.style.opacity = '0';
            matchElement.style.maxHeight = '0px';
            matchElement.style.marginTop = '0';
            matchElement.style.marginBottom = '0';
            matchElement.style.paddingTop = '0';
            matchElement.style.paddingBottom = '0';
            matchElement.style.borderWidth = '0';

            setTimeout(() => {
                const listContainer = matchElement.parentElement;
                matchElement.remove();

                const noMatchesMessage = document.getElementById("no-matches-message-history"); // Adjust ID if needed for different pages
                if (listContainer && noMatchesMessage && listContainer.children.length === 0) {
                     noMatchesMessage.classList.remove('hidden');
                }

                if (typeof showFlashMessage === 'function') showFlashMessage("Match hidden successfully.", "success");

                // Execute the callback after successful deletion and removal
                if (typeof onMatchDeletedCallback === 'function') {
                    onMatchDeletedCallback();
                }

            }, 300);
        } else {
             if (deleteButton && document.body.contains(deleteButton)) {
                deleteButton.disabled = false;
                deleteButton.innerHTML = `<svg class="mr-3 h-5 w-5 text-red-400 group-hover:text-red-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd" /></svg>Delete Match`;
            }
        }
    });
}

// --- Action Menu Utility ---
function closeAllActionMenus(exceptMenu = null) {
    document.querySelectorAll('.match-action-menu').forEach(menu => {
        if (menu !== exceptMenu && !menu.classList.contains('hidden')) {
            menu.classList.add('hidden');
            const button = menu.closest('.match-item')?.querySelector('.match-options-btn');
            if (button) button.setAttribute('aria-expanded', 'false');
        }
    });
}

// --- Initialization and Event Handling ---
let containerListeners = new Map(); // Stores listeners per container to prevent duplicates
let globalClickListener = null;     // Stores the single global listener for closing menus

function initializeMatchActionMenus(containerId, onMatchDeletedCallback) {
    const listContainer = document.getElementById(containerId);
    if (!listContainer) {
        console.error(`Match action initializer: Container #${containerId} not found.`);
        return;
    }

    // Define the click handler for actions within this container
    const handleContainerClick = (event) => {
        const optionsButton = event.target.closest('.match-options-btn');
        const deleteButton = event.target.closest('.menu-delete-match-btn');
        const matchItemElement = event.target.closest('.match-item');

        if (!matchItemElement) return; // Ignore clicks not on relevant elements

        // Handle menu toggle clicks
        if (optionsButton) {
            event.stopPropagation();
            const menu = matchItemElement.querySelector('.match-action-menu');
            if (menu) {
                const isHidden = menu.classList.contains('hidden');
                closeAllActionMenus(menu); // Close other menus
                menu.classList.toggle('hidden', !isHidden);
                optionsButton.setAttribute('aria-expanded', String(isHidden));
            }
            return;
        }

        // Handle delete button clicks
        if (deleteButton) {
            event.stopPropagation();
            const matchId = deleteButton.dataset.matchId;
            closeAllActionMenus(); // Close menu before confirmation
            if (matchId) {
                // Pass the callback down to the confirmation logic
                showDeleteMatchConfirmation(matchId, matchItemElement, onMatchDeletedCallback);
            }
            return;
        }
    };

    // Remove any previous listener attached to this specific container
    const oldListener = containerListeners.get(containerId);
    if (oldListener) {
        listContainer.removeEventListener('click', oldListener);
    }

    // Add the new listener for this container
    listContainer.addEventListener('click', handleContainerClick);
    containerListeners.set(containerId, handleContainerClick); // Remember the listener

    // Setup the global listener to close menus on outside clicks (only once)
    if (!globalClickListener) {
        globalClickListener = (event) => {
            if (!event.target.closest('.match-actions')) {
                closeAllActionMenus();
            }
        };
        document.addEventListener('click', globalClickListener);
    }
}

// --- Export ---
export { initializeMatchActionMenus };