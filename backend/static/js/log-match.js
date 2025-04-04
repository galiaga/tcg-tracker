import { authFetch } from './auth/auth.js';
import { updateMatchHistoryView } from './ui/matches/match-list-manager.js';
import { TagInputManager } from './ui/tagInput.js';
import { populateTagFilter } from './ui/matches/filter-matches-by-tag.js';

let matchTagInputInstance = null;

document.addEventListener("DOMContentLoaded", () => {
    populateDeckSelect();

    const logMatchForm = document.getElementById("log-match-form");
    if (logMatchForm) {
        logMatchForm.addEventListener("submit", handleLogMatchSubmit);
    } else {
         console.warn("log-match.js: Log match form not found in this view.");
    }

    const openModalBtn = document.getElementById('logMatchModalButton');
    const modal = document.getElementById('logMatchModal');
    const closeModalBtn = document.getElementById('logMatchModalCloseButton');

     function initializeTagInput() {
         if (typeof TagInputManager !== 'undefined') {
             matchTagInputInstance = TagInputManager.init({
                 inputId: 'match-tags-input',
                 suggestionsId: 'match-tags-suggestions',
                 containerId: 'match-tags-container'
             });
             if (matchTagInputInstance) {
                 matchTagInputInstance.clearTags();
             } else {
                  console.error("Failed to initialize TagInputManager for matches.");
             }
         } else {
              console.warn("TagInputManager not loaded before log-match.js attempted init.");
         }
     }

     function clearTagInput() {
          if (matchTagInputInstance) {
              matchTagInputInstance.clearTags();
          }
     }

     if (openModalBtn) {
         openModalBtn.addEventListener('click', initializeTagInput);
     } else {
         console.warn("Button 'logMatchModalButton' not found for tag input init binding.");
     }
     if (closeModalBtn) {
          closeModalBtn.addEventListener('click', clearTagInput);
     }
      if (modal) {
         modal.addEventListener('click', (event) => {
            if (event.target === modal) {
                clearTagInput();
            }
         });
      }

});

async function populateDeckSelect() {
    const deckSelect = document.getElementById("deck-select");
    if (!deckSelect) return;

    deckSelect.disabled = true;
    const originalOption = '<option disabled selected value="">Select Deck</option>';
    deckSelect.innerHTML = '<option disabled selected value="">Loading decks...</option>';

    try {
        const response = await authFetch("/api/user_decks");
        if (!response || !response.ok) {
            const errorData = response ? await response.json().catch(() => ({})) : {};
            throw new Error(errorData.error || `Failed to fetch decks (${response?.status})`);
        }
        const decks = await response.json();

        deckSelect.innerHTML = originalOption;

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

    const selectedTagIds = matchTagInputInstance ? matchTagInputInstance.getSelectedTagIds() : [];

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
            const newMatchId = data.match?.id;
            let associationErrors = false;

            if (newMatchId && selectedTagIds.length > 0) {
                 const associationPromises = selectedTagIds.map(tagId => {
                     return authFetch(`/api/matches/${newMatchId}/tags`, {
                         method: 'POST',
                         body: JSON.stringify({ tag_id: tagId })
                     }).catch(err => {
                          console.error(`Error associating tag ${tagId} with match ${newMatchId}:`, err);
                          associationErrors = true;
                          return null;
                     });
                 });
                 await Promise.all(associationPromises);
            }

            let successMessage = `${matchResultText} with ${deckName} registered!`;
             if (associationErrors) {
                  successMessage += " (Note: Some tags might not have been associated due to errors - check console).";
             }
             if (typeof showFlashMessage === 'function') {
                 showFlashMessage(successMessage, associationErrors ? "warning" : "success");
             }

            form.dispatchEvent(new CustomEvent('matchLoggedSuccess'));

            if (typeof updateMatchHistoryView === 'function') {
                updateMatchHistoryView();
                 if(typeof populateTagFilter === 'function') {
                     populateTagFilter();
                 }
            } else {
                 console.warn("updateMatchHistoryView function not available to reload history.");
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