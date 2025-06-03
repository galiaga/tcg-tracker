// backend/static/js/ui/matches/log-match.js
import { authFetch } from '../../auth/auth.js';
import { updateMatchHistoryView } from './match-list-manager.js';
// Import functions from log-match-modal.js
import { openLogMatchModal, getMatchTagInputInstance } from './log-match-modal.js';

// --- DOM Element References (fetched once DOM is ready) ---
let logMatchFormElement = null;
let deckSelectElement = null; // For populating decks

// --- Deck Population ---
async function populateDeckSelect() {
    const currentDeckSelect = deckSelectElement || document.getElementById("deck-select"); // Fallback if not initialized
    if (!currentDeckSelect) {
        console.warn("[log-match.js] Deck select element #deck-select not found for populateDeckSelect.");
        return;
    }
    currentDeckSelect.disabled = true;
    const originalOptionHTML = '<option disabled selected value="">Select Deck</option>';
    currentDeckSelect.innerHTML = '<option disabled selected value="">Loading decks...</option>';
    try {
        const response = await authFetch("/api/user_decks");
        if (!response || !response.ok) {
             const errorData = response ? await response.json().catch(() => ({})) : {};
             throw new Error(errorData.error || `Failed to fetch decks (${response?.status})`);
         }
        const decks = await response.json();
        currentDeckSelect.innerHTML = originalOptionHTML;
        if (Array.isArray(decks) && decks.length > 0) {
            decks.forEach(deck => {
                const option = document.createElement("option");
                option.value = deck.id;
                option.dataset.name = deck.name;
                option.textContent = deck.name;
                currentDeckSelect.appendChild(option);
            });
             currentDeckSelect.disabled = false;
        } else {
             currentDeckSelect.innerHTML = '<option disabled selected value="">No decks available</option>';
        }
        document.dispatchEvent(new CustomEvent('deckOptionsLoaded'));
    } catch (error) {
        console.error("Failed to fetch decks for log match:", error);
        if (currentDeckSelect) currentDeckSelect.innerHTML = '<option disabled selected value="">Could not load decks</option>';
         if (typeof showFlashMessage === 'function') {
             showFlashMessage(error.message || "Could not load your decks.", "danger");
         }
    }
}

// --- Form Submission ---
async function handleLogMatchSubmit(event) {
    event.preventDefault();
    const form = event.target; // Should be logMatchFormElement

    const currentDeckSelect = form.querySelector("#deck-select");
    const selectedResultRadio = form.querySelector('input[name="match_result"]:checked');
    const selectedPositionRadio = form.querySelector('input[name="player_position_radio"]:checked');
    const opponentDescriptionInput = form.querySelector("#log-match-opponent-description");
    const submitButton = form.querySelector('button[type="submit"]');

    if (!currentDeckSelect || !selectedResultRadio || !submitButton) {
        if (typeof showFlashMessage === 'function') showFlashMessage("Form elements missing (deck, result, or submit). Please refresh.", "danger");
        console.error("Log match form elements missing (deck select, result radio, or submit button).");
        return;
    }
    if (!selectedPositionRadio) {
        if (typeof showFlashMessage === 'function') showFlashMessage("Please select your turn position.", "warning");
        console.error("Player position radio not selected.");
        return;
    }

    const deckId = currentDeckSelect.value;
    const selectedOption = currentDeckSelect.options[currentDeckSelect.selectedIndex];
    const deckName = selectedOption?.dataset.name ?? 'Selected Deck';
    const resultValue = selectedResultRadio.value;
    const playerPositionValue = selectedPositionRadio.value;
    const opponentDescription = opponentDescriptionInput ? opponentDescriptionInput.value.trim() : null;

    if (!deckId || !deckId.trim() || (selectedOption && selectedOption.disabled)) {
        if (typeof showFlashMessage === 'function') showFlashMessage("Please select a valid deck.", "warning");
        return;
    }

    const tagInputInstance = getMatchTagInputInstance();
    const selectedTagIds = (tagInputInstance) ? tagInputInstance.getSelectedTagIds() : [];

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
            if (form) form.reset();
            if (currentDeckSelect && currentDeckSelect.options.length > 0) currentDeckSelect.value = "";
            const defaultResultRadio = form.querySelector('input[name="match_result"][value="0"]');
            if (defaultResultRadio) defaultResultRadio.checked = true;

            form.dispatchEvent(new CustomEvent('matchLoggedSuccess', { detail: { matchId: data.match?.id } }));
            if (typeof updateMatchHistoryView === 'function') {
                updateMatchHistoryView();
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
    // Get the form element. The submit listener will be attached to this.
    logMatchFormElement = document.getElementById("log-match-form");
    if (logMatchFormElement) {
        // Get the deck select element within the form for populating it.
        deckSelectElement = logMatchFormElement.querySelector("#deck-select");
        
        logMatchFormElement.addEventListener("submit", handleLogMatchSubmit);
        populateDeckSelect(); // Populate decks as the form exists.
    } else {
        // This is expected if the modal (and thus the form) is not in the current page's static HTML
        // but included via a partial that might not be rendered on all pages.
        // console.info("log-match.js: Log match form #log-match-form not found on this page. Submit listener not attached.");
    }

    // Get the button that opens the modal. This button might be on specific pages like matches-history.html
    const mainLogMatchButtonElement = document.getElementById('logMatchModalButton');
    if (mainLogMatchButtonElement) {
        if (typeof openLogMatchModal === 'function') {
            mainLogMatchButtonElement.addEventListener('click', () => {
                console.log("[log-match.js] Main Log Match Button (id='logMatchModalButton') clicked, attempting to open modal.");
                openLogMatchModal(); // This function is from log-match-modal.js
            });
        } else {
            console.warn("[log-match.js] Main Log Match Modal button found, but openLogMatchModal function is not available/imported correctly.");
        }
    } else {
        // This is normal if this specific button isn't on the current page.
        // console.info("[log-match.js] Main Log Match Modal button with ID 'logMatchModalButton' not found on this page.");
    }
}

document.addEventListener("DOMContentLoaded", () => {
    initializeLogMatchScript();
});