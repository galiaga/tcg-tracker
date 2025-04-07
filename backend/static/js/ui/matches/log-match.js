import { authFetch } from '../../auth/auth.js';
import { updateMatchHistoryView } from './match-list-manager.js';
import { TagInputManager } from '../tagInput.js';
import { populateTagFilter } from './filter-matches-by-tag.js';
import { openLogMatchModal } from './log-match-modal.js'; 

let matchTagInputInstance = null;

window.initializeMatchTagInput = function() {
     if (matchTagInputInstance) {
          matchTagInputInstance.clearTags();
     }
     if (typeof TagInputManager !== 'undefined') {
         matchTagInputInstance = TagInputManager.init({
             inputId: 'match-tags-input',
             suggestionsId: 'match-tags-suggestions',
             containerId: 'match-tags-container'
         });
         if (!matchTagInputInstance) {
             console.error("Failed to initialize TagInputManager for matches.");
         }
     } else {
         console.warn("TagInputManager not loaded before log-match.js attempted init.");
     }
 }

 window.clearMatchTagInput = function() {
     if (matchTagInputInstance) {
         matchTagInputInstance.clearTags();
     }
 }


document.addEventListener("DOMContentLoaded", () => {
    populateDeckSelect();

    const logMatchForm = document.getElementById("log-match-form");
    if (logMatchForm) {
        logMatchForm.addEventListener("submit", handleLogMatchSubmit);
    } else {
        console.warn("log-match.js: Log match form not found in this view.");
    }

    const mainLogMatchButton = document.getElementById('logMatchModalButton');
    if(mainLogMatchButton){
       mainLogMatchButton.addEventListener('click', () => openLogMatchModal());
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

       const selectedTagIds = (typeof matchTagInputInstance !== 'undefined' && matchTagInputInstance)
                            ? matchTagInputInstance.getSelectedTagIds()
                            : [];

       const payload = {
           deck_id: parseInt(deckId, 10),
           match_result: parseInt(resultValue, 10) 
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
                      successMessage += " (Note: Some tags might not have been associated).";
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