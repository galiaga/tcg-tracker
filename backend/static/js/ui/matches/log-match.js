// backend/static/js/ui/matches/log-match.js

import { authFetch } from '../../auth/auth.js';
import { updateMatchHistoryView } from './match-list-manager.js';
// Import functions from log-match-modal.js
// REMOVED: populateDeckSelect as populateModalDeckSelect (it's now internal to log-match-modal.js)
import { openLogMatchModal, getSelectedTagIdsForCurrentMatch } from './log-match-modal.js';

// --- DOM Element References ---
let logMatchFormElement = null; // This will be the form from the modal

// --- Deck Population ---
// populateDeckSelect function has been MOVED to log-match-modal.js

// --- Form Submission ---
async function handleLogMatchSubmit(event) {
    event.preventDefault();
    const form = event.target;

    const currentDeckSelect = form.querySelector("#deck-select");
    const selectedResultRadio = form.querySelector('input[name="match_result"]:checked');
    const selectedPositionRadio = form.querySelector('input[name="player_position_radio"]:checked');
    const opponentDescriptionInput = form.querySelector("#log-match-opponent-description");
    const submitButton = form.querySelector('button[type="submit"]');

    // --- MODIFIED VALIDATION ---
    // 1. Check for essential structural form elements first
    if (!currentDeckSelect || !submitButton) { // Result radio has a default, position is checked next
        if (typeof showFlashMessage === 'function') {
            showFlashMessage("Critical form elements are missing. Please try refreshing the page.", "danger");
        }
        console.error("Log match form: Deck select or submit button missing.");
        return;
    }

    // 2. Check for selected deck
    const deckId = currentDeckSelect.value;
    const selectedOption = currentDeckSelect.options[currentDeckSelect.selectedIndex];
    if (!deckId || !deckId.trim() || (selectedOption && selectedOption.disabled)) {
        if (typeof showFlashMessage === 'function') showFlashMessage("Please select a valid deck.", "warning");
        return;
    }
    
    // 3. Check for selected result (though it has a default, good to keep a check)
    if (!selectedResultRadio) {
        if (typeof showFlashMessage === 'function') showFlashMessage("Please select the match result.", "warning");
        // This case should be rare now since "Win" is default checked in HTML
        return; 
    }

    // 4. Check for selected player position - THIS IS THE SPECIFIC CHECK
    if (!selectedPositionRadio) {
        if (typeof showFlashMessage === 'function') {
            showFlashMessage("Please select your turn order (player position).", "warning"); // Specific message
        }
        // Optionally, focus the first player position button or its label
        const firstPositionLabel = form.querySelector('label[for="log-match-pos-1"]');
        firstPositionLabel?.focus();
        return;
    }
    // --- END OF MODIFIED VALIDATION ---


    const deckName = selectedOption?.dataset.name ?? 'Selected Deck';
    const resultValue = selectedResultRadio.value;
    const playerPositionValue = selectedPositionRadio.value;
    const opponentDescription = opponentDescriptionInput ? opponentDescriptionInput.value.trim() : null;

    const selectedTagIds = getSelectedTagIdsForCurrentMatch();

    const payload = {
        deck_id: parseInt(deckId, 10),
        result: parseInt(resultValue, 10),
        player_position: parseInt(playerPositionValue, 10),
        tags: selectedTagIds
    };
    if (opponentDescription) {
        payload.opponent_description = opponentDescription;
    }

    const resultMapping = { "0": "Win", "1": "Loss", "2": "Draw" };
    const matchResultText = resultMapping[resultValue] ?? 'Result';
    const originalButtonText = submitButton.textContent;
    submitButton.disabled = true;
    submitButton.innerHTML = `<span class="spinner-tiny inline-block mr-2"></span>Logging...`;

    try {
        const response = await authFetch("/api/log_match", {
            method: "POST",
            body: JSON.stringify(payload)
        });
        if (!response) throw new Error("Network or Authentication Error during match log.");
        const data = await response.json();
        if (response.ok) {
            if (typeof showFlashMessage === 'function') {
                showFlashMessage(`${matchResultText} with ${deckName} registered!`, "success");
            }
            
            document.dispatchEvent(new CustomEvent('globalMatchLoggedSuccess', { 
                detail: { 
                    matchId: data.match?.id,
                    deckId: payload.deck_id 
                } 
            }));

            const isOnMyMatchesPage = document.getElementById('matches-list-items') && 
                                      !document.getElementById('deck-details');
         
            if (isOnMyMatchesPage) {
                if (typeof updateMatchHistoryView === 'function') {
                    updateMatchHistoryView();
                }
            }

            if (form) {
                 form.dispatchEvent(new CustomEvent('matchLoggedSuccess', { detail: { matchId: data.match?.id } }));
            }

        } else {
            throw new Error(data.error || `Error logging match: ${response.statusText}`);
        }
    } catch (error) {
        console.error("Error submitting match:", error);
        if (typeof showFlashMessage === 'function') {
            showFlashMessage(error.message || "An unexpected error occurred.", "danger");
        }
    } finally {
        if (submitButton) {
            submitButton.disabled = false;
            submitButton.textContent = originalButtonText;
        }
    }
}

// --- Event Listeners & Initialization ---
function initializeLogMatchScript() {
    // Get the form from the modal AFTER the modal's own JS has initialized it.
    // The listener is now added in log-match-modal.js's initializeModal if formElement is found.
    // However, it's safer if log-match.js (which owns submit logic) adds it.
    // Let's ensure logMatchFormElement is set up here if the modal is present.

    logMatchFormElement = document.getElementById("log-match-form");
    if (logMatchFormElement) {
        // Remove existing listener to prevent duplicates if this script runs multiple times
        logMatchFormElement.removeEventListener("submit", handleLogMatchSubmit);
        logMatchFormElement.addEventListener("submit", handleLogMatchSubmit);
    } else {
        // This might happen if the modal is not in the DOM when this script runs.
        // log-match-modal.js's initializeModal should find it.
    }


    const mainLogMatchButtonElement = document.getElementById('logMatchModalButton');
    if (mainLogMatchButtonElement) {
        if (typeof openLogMatchModal === 'function') {
            mainLogMatchButtonElement.addEventListener('click', () => {
                // openLogMatchModal now handles its own deck population
                openLogMatchModal(); 
            });
        } else {
            console.warn("[log-match.js] Main Log Match Modal button found, but openLogMatchModal function is not available.");
        }
    }
}

document.addEventListener("DOMContentLoaded", () => {
    initializeLogMatchScript();
});

// No need to export populateDeckSelect from here anymore
// handleLogMatchSubmit might not need to be exported if the event listener is always set up here.
// However, if log-match-modal.js *needs* to directly call it (e.g. if it had its own submit button), then export.
// For now, assuming the form's submit event is the sole trigger.