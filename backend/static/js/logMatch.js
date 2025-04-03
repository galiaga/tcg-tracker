import { authFetch } from './auth/auth.js';
import { loadUserMatches } from './api/match_history.js';

document.addEventListener("DOMContentLoaded", () => {
    populateDeckSelect();

    const logMatchForm = document.getElementById("log-match-form");
    if (logMatchForm) {
        logMatchForm.addEventListener("submit", handleLogMatchSubmit);
    } else {
         console.warn("logMatch.js: Log match form not found in this view.");
    }
});

async function populateDeckSelect() {
    const deckSelect = document.getElementById("deck-select");
    if (!deckSelect) return;

    deckSelect.disabled = true;

    try {
        const response = await authFetch("/api/user_decks");
        if (!response || !response.ok) {
            const errorData = response ? await response.json().catch(() => ({})) : {};
            throw new Error(errorData.error || `Failed to fetch decks (${response?.status})`);
        }
        const decks = await response.json();

        deckSelect.innerHTML = '<option disabled selected value="">Select Deck</option>';

        if (Array.isArray(decks) && decks.length > 0) {
            decks.forEach(deck => {
                const option = document.createElement("option");
                option.value = deck.id;
                option.dataset.name = deck.name;
                option.textContent = deck.name;
                deckSelect.appendChild(option);
            });
             deckSelect.disabled = false;
        } else {
             console.warn("Received no decks or non-array response:", decks);
             deckSelect.innerHTML = '<option disabled selected value="">No decks available</option>';
        }

    } catch (error) {
        console.error("Failed to fetch decks:", error);
        deckSelect.innerHTML = '<option disabled selected value="">Could not load decks</option>';
         if (typeof showFlashMessage === 'function') {
            showFlashMessage(error.message || "Could not load your decks.", "danger");
        }
    }
}

async function handleLogMatchSubmit(event) {
    event.preventDefault();
    const form = event.target;
    const deckSelect = document.getElementById("deck-select");
    const selectedResultRadio = form.querySelector('input[name="match_result"]:checked');
    const submitButton = form.querySelector('button[type="submit"]');

    if (!deckSelect || !selectedResultRadio || !submitButton) {
         if (typeof showFlashMessage === 'function') {
             showFlashMessage("Form elements missing.", "danger");
         }
        return;
    }

    const deckId = deckSelect.value;
    const selectedOption = deckSelect.options[deckSelect.selectedIndex];
    const deckName = selectedOption?.dataset.name ?? 'Selected Deck';
    const resultValue = selectedResultRadio.value;

    if (!deckId || selectedOption.disabled) {
         if (typeof showFlashMessage === 'function') {
             showFlashMessage("Please select a valid deck.", "warning");
         }
        return;
    }

    const payload = {
        deck_id: deckId,
        match_result: resultValue
    };

    const resultMapping = { "0": "Victory", "1": "Defeat", "2": "Draw" };
    const matchResultText = resultMapping[resultValue] ?? 'Result';
    const originalButtonText = submitButton.textContent;
    submitButton.disabled = true;
    submitButton.textContent = 'Logging...';

    try {
        const response = await authFetch("/api/log_match", {
            method: "POST",
            body: JSON.stringify(payload)
        });

        if (!response) return;

        const data = await response.json();

        if (response.ok) {
             if (typeof showFlashMessage === 'function') {
                 showFlashMessage(`${matchResultText} with ${deckName} registered!`, "success");
             }
             form.dispatchEvent(new CustomEvent('matchLoggedSuccess'));
             if (typeof loadUserMatches === 'function') {
                 loadUserMatches();
             } else {
                  console.warn("loadUserMatches function not available to reload history.");
             }
        } else {
              if (typeof showFlashMessage === 'function') {
                  showFlashMessage(data.error || `Error logging match: ${response.statusText}`, "danger");
              }
        }
    } catch (error) {
        console.error("Error submitting match:", error);
         if (typeof showFlashMessage === 'function') {
             showFlashMessage(error.message || "An unexpected error occurred.", "danger");
         }
    } finally {
         submitButton.disabled = false;
         submitButton.textContent = originalButtonText;
    }
}