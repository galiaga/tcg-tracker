import { authFetch } from '../../auth/auth.js';
import { updateMatchHistoryView } from './match-list-manager.js';
// Import getOpponentCommandersData
import { openLogMatchModal, getSelectedTagIdsForCurrentMatch, getOpponentCommandersData } from './log-match-modal.js';

let logMatchFormElement = null;

async function handleLogMatchSubmit(event) {
    console.log("[log-match.js] handleLogMatchSubmit called.");
    event.preventDefault();
    const form = event.target;

    const currentDeckSelect = form.querySelector("#deck-select");
    const selectedResultRadio = form.querySelector('input[name="match_result"]:checked');
    const selectedPositionRadio = form.querySelector('input[name="player_position_radio"]:checked');
    const selectedMulliganRadio = form.querySelector('input[name="player_mulligans_radio"]:checked');
    const submitButton = form.querySelector('button[type="submit"]');
    const podNotesInput = form.querySelector('#log-match-pod-notes');

    if (!currentDeckSelect || !submitButton) {
        if (typeof showFlashMessage === 'function') showFlashMessage("Critical form elements are missing.", "danger");
        return;
    }
    const deckId = currentDeckSelect.value;
    const selectedOption = currentDeckSelect.options[currentDeckSelect.selectedIndex];
    if (!deckId || !deckId.trim() || (selectedOption && selectedOption.disabled)) {
        if (typeof showFlashMessage === 'function') showFlashMessage("Please select a valid deck.", "warning");
        currentDeckSelect.focus(); return;
    }
    if (!selectedResultRadio) {
        if (typeof showFlashMessage === 'function') showFlashMessage("Please select the match result.", "warning");
        form.querySelector('label[for="log-match-result-win"]')?.focus(); return; 
    }
    if (!selectedPositionRadio) {
        if (typeof showFlashMessage === 'function') showFlashMessage("Please select your turn order.", "warning");
        form.querySelector('label[for="log-match-pos-1"]')?.focus(); return;
    }

    const deckName = selectedOption?.dataset.name ?? 'Selected Deck';
    const resultValue = selectedResultRadio.value;
    const playerPositionValue = selectedPositionRadio.value;
    
    let playerMulligansValue = null;
    if (selectedMulliganRadio) {
        playerMulligansValue = parseInt(selectedMulliganRadio.value, 10);
        if (isNaN(playerMulligansValue)) playerMulligansValue = null; 
    }
    
    const opponentCommandersDataForPayload = getOpponentCommandersData(); // Get structured data
    
    const podNotesValue = podNotesInput?.value.trim() || null;
    const selectedTagIds = getSelectedTagIdsForCurrentMatch();

    const payload = {
        deck_id: parseInt(deckId, 10),
        result: parseInt(resultValue, 10),
        player_position: parseInt(playerPositionValue, 10),
        player_mulligans: playerMulligansValue,
        opponent_commanders_by_seat: opponentCommandersDataForPayload, // Use the new structured data
        pod_notes: podNotesValue,
        tags: selectedTagIds
    };

    const resultMapping = { "0": "Win", "1": "Loss", "2": "Draw" };
    const matchResultText = resultMapping[resultValue] ?? 'Result';
    const originalButtonText = submitButton.textContent;
    submitButton.disabled = true;
    submitButton.innerHTML = `<span class="spinner-tiny inline-block mr-2"></span>Logging...`;

    console.log("SUBMITTING PAYLOAD TO /api/log_match:", JSON.stringify(payload, null, 2)); 

    try {
        const response = await authFetch("/api/log_match", {
            method: "POST",
            body: JSON.stringify(payload)
        });
        if (!response) throw new Error("Network or Authentication Error during match log.");
        const data = await response.json();
        if (response.ok) {
            if (typeof showFlashMessage === 'function') showFlashMessage(`${matchResultText} with ${deckName} registered!`, "success");
            document.dispatchEvent(new CustomEvent('globalMatchLoggedSuccess', { detail: { matchId: data.match?.id, deckId: payload.deck_id } }));
            const isOnMyMatchesPage = document.getElementById('matches-list-items') && !document.getElementById('deck-details');
            if (isOnMyMatchesPage && typeof updateMatchHistoryView === 'function') updateMatchHistoryView();
            if (form) form.dispatchEvent(new CustomEvent('matchLoggedSuccess', { detail: { matchId: data.match?.id } }));
        } else {
            throw new Error(data.error || data.details || `Error logging match: ${response.statusText}`);
        }
    } catch (error) {
        console.error("Error submitting match:", error);
        if (typeof showFlashMessage === 'function') showFlashMessage(error.message || "An unexpected error occurred.", "danger");
    } finally {
        if (submitButton) {
            submitButton.disabled = false;
            submitButton.textContent = originalButtonText;
        }
    }
}

function initializeLogMatchScript() {
    console.log("[log-match.js] initializeLogMatchScript called."); // ADD
    logMatchFormElement = document.getElementById("log-match-form");
    if (logMatchFormElement) {
        logMatchFormElement.removeEventListener("submit", handleLogMatchSubmit);
        logMatchFormElement.addEventListener("submit", handleLogMatchSubmit);
        console.log("[log-match.js] Submit event listener ATTACHED to #log-match-form"); // ADD
    } else {
        console.error("[log-match.js] #log-match-form NOT FOUND during initializeLogMatchScript. Cannot attach submit listener.");
    }
    const mainLogMatchButtonElement = document.getElementById('logMatchModalButton');
    if (mainLogMatchButtonElement && typeof openLogMatchModal === 'function') {
        mainLogMatchButtonElement.addEventListener('click', () => openLogMatchModal());
    }
}

document.addEventListener("DOMContentLoaded", () => {
    console.log("[log-match.js] DOMContentLoaded event fired. Initializing script...");
    initializeLogMatchScript();
});