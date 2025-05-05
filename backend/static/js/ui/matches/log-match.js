import { authFetch } from '../../auth/auth.js';
import { updateMatchHistoryView } from './match-list-manager.js';
import { TagInputManager } from '../tagInput.js';
import { openLogMatchModal } from './log-match-modal.js';

let matchTagInputInstance = null;

export function initializeTagInputForModal() {
    if (matchTagInputInstance) {
        matchTagInputInstance.clearTags();
    }
    if (typeof TagInputManager !== 'undefined' && typeof TagInputManager.init === 'function') {
        matchTagInputInstance = TagInputManager.init({
            inputId: 'match-tags-input',
            suggestionsId: 'match-tags-suggestions',
            containerId: 'match-tags-container'
        });
        if (!matchTagInputInstance) {
            console.error("Failed to initialize TagInputManager for match modal.");
        }
    } else {
        console.error("TagInputManager or TagInputManager.init function not available.");
    }
}

export function clearTagInputForModal() {
     if (matchTagInputInstance) {
         matchTagInputInstance.clearTags();
     }
}

async function populateDeckSelect() {
    const deckSelect = document.getElementById("deck-select");
    if (!deckSelect) return;

    deckSelect.disabled = true;
    const originalOptionHTML = '<option disabled selected value="">Select Deck</option>';
    deckSelect.innerHTML = '<option disabled selected value="">Loading decks...</option>';

    try {
        const response = await authFetch("/api/user_decks");
        if (!response || !response.ok) {
             const errorData = response ? await response.json().catch(() => ({})) : {};
             throw new Error(errorData.error || `Failed to fetch decks (${response?.status})`);
         }
        const decks = await response.json();

        deckSelect.innerHTML = originalOptionHTML;

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
             deckSelect.innerHTML = '<option disabled selected value="">No decks available</option>';
        }
        document.dispatchEvent(new CustomEvent('deckOptionsLoaded'));

    } catch (error) {
        console.error("Failed to fetch decks for log match:", error);
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
        console.error("Log match form elements missing.");
        return;
    }

    const deckId = deckSelect.value;
    const selectedOption = deckSelect.options[deckSelect.selectedIndex];
    const deckName = selectedOption?.dataset.name ?? 'Selected Deck';
    const resultValue = selectedResultRadio.value;

    if (!deckId || !deckId.trim() || (selectedOption && selectedOption.disabled)) {
        if (typeof showFlashMessage === 'function') {
            showFlashMessage("Please select a valid deck.", "warning");
        }
        return;
    }

    const selectedTagIds = (matchTagInputInstance)
                            ? matchTagInputInstance.getSelectedTagIds()
                            : [];

    const payload = {
        deck_id: parseInt(deckId, 10),
        result: parseInt(resultValue, 10)
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

        if (!response) throw new Error("Network or Authentication Error during match log.");

        const data = await response.json();

        if (response.ok) {
            const newMatchId = data.match?.id;
            let associationErrors = false;

            if (newMatchId && selectedTagIds.length > 0) {
                const associationPromises = selectedTagIds.map(tagId => {
                    return authFetch(`/api/matches/${newMatchId}/tags`, {
                        method: 'POST',
                        body: JSON.stringify({ tag_id: parseInt(tagId, 10) })
                    }).then(res => {
                        if (!res.ok) {
                             console.error(`Failed to associate tag ${tagId} with match ${newMatchId}. Status: ${res.status}`);
                             associationErrors = true;
                        }
                        return res;
                    }).catch(err => {
                         console.error(`Network error associating tag ${tagId} with match ${newMatchId}:`, err);
                         associationErrors = true;
                         return null;
                     });
                });
                await Promise.all(associationPromises);
            }

            let successMessage = `${matchResultText} with ${deckName} registered!`;
            if (associationErrors) {
                successMessage += " (Note: Some tags might not have been associated).";
            }
            if (typeof showFlashMessage === 'function') {
                showFlashMessage(successMessage, associationErrors ? "warning" : "success");
            }

            clearTagInputForModal();

            form.dispatchEvent(new CustomEvent('matchLoggedSuccess', { detail: { matchId: newMatchId } }));

            if (typeof updateMatchHistoryView === 'function') {
                updateMatchHistoryView();
            } else {
                console.warn("updateMatchHistoryView function not available to reload history.");
            }

            if(typeof closeLogMatchModal === 'function'){
                 closeLogMatchModal();
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
        submitButton.disabled = false;
        submitButton.textContent = originalButtonText;
    }
}


document.addEventListener("DOMContentLoaded", () => {
    populateDeckSelect();

    const logMatchForm = document.getElementById("log-match-form");
    if (logMatchForm) {
        logMatchForm.addEventListener("submit", handleLogMatchSubmit);
    } else {
        console.warn("log-match.js: Log match form not found.");
    }

    const mainLogMatchButton = document.getElementById('logMatchModalButton');
    if (mainLogMatchButton && typeof openLogMatchModal === 'function') {
       mainLogMatchButton.addEventListener('click', () => {
            openLogMatchModal();
            initializeTagInputForModal(); 
       });
    } else if (mainLogMatchButton) {
        console.warn("Log match modal button found, but openLogMatchModal function is not available/imported.");
    }

});