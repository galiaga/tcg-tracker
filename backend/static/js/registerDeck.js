import { authFetch } from './auth/auth.js';
import { TagInputManager } from './ui/tagInput.js';

const COMMANDER_DECK_TYPE_ID = "7";
let deckTagInputInstance = null;

// --- Tag Input Management ---
function initializeTagInput() {
    if (typeof TagInputManager !== 'undefined') {
        // Only initialize if not already done
        if (!deckTagInputInstance) {
            deckTagInputInstance = TagInputManager.init({
                inputId: 'deck-tags-input',
                suggestionsId: 'deck-tags-suggestions',
                containerId: 'deck-tags-container'
            });
        }
        // Ensure it's clear on init (though reset logic should handle it too)
        if (deckTagInputInstance) {
            deckTagInputInstance.clearTags();
        } else {
             console.error("Failed to initialize TagInputManager for decks.");
        }
    } else {
         console.warn("TagInputManager not loaded when registerDeck.js attempted init.");
    }
}

function clearTagInput() {
     if (deckTagInputInstance) {
         deckTagInputInstance.clearTags();
     } else {
         // Fallback manual clear
         const tagContainer = document.getElementById('deck-tags-container');
         const tagInput = document.getElementById('deck-tags-input');
         const tagSuggestions = document.getElementById('deck-tags-suggestions');
         if (tagContainer) tagContainer.innerHTML = '';
         if (tagInput) tagInput.value = '';
         if (tagSuggestions) {
             tagSuggestions.innerHTML = '';
             tagSuggestions.classList.add('hidden');
         }
     }
}

document.addEventListener("DOMContentLoaded", function() {
    const registerForm = document.getElementById("register-deck-form");
    if (!registerForm) return;

    // Initialization is now primarily handled by new-deck-modal.js on open

    // --- Form Submission ---
    registerForm.addEventListener("submit", async function(event) {
        event.preventDefault();

        // Ensure tag instance exists before trying to get tags
        if (!deckTagInputInstance) {
             console.warn("TagInputManager instance missing during submit. Attempting re-init.");
             initializeTagInput(); // Try to get it
             if (!deckTagInputInstance) {
                  console.error("Cannot submit: TagInputManager instance is unavailable.");
                  // Optionally show user error: if (typeof showFlashMessage === 'function') showFlashMessage("Tag input error. Please close and reopen the modal.", "error");
                  return;
             }
        }

        const deckTypeElement = document.getElementById("deck_type");
        const deckNameElement = document.getElementById("deck_name");
        const commanderInputElement = document.getElementById("commander_name");
        const partnerInputElement = document.getElementById("partner_name");
        const friendsForeverInputElement = document.getElementById("friendsForever_name");
        const doctorCompanionInputElement = document.getElementById("doctorCompanion_name");
        const timeLordDoctorInputElement = document.getElementById("timeLordDoctor_name");
        const backgroundInputElement = document.getElementById("chooseABackground_name");

        const deckTypeId = deckTypeElement ? deckTypeElement.value : null;
        const deckName = deckNameElement ? deckNameElement.value.trim() : "";

        if (!deckName) {
            if (typeof showFlashMessage === 'function') showFlashMessage("Please enter a Deck Name.", "error");
            return;
        }
        if (!deckTypeId) {
            if (typeof showFlashMessage === 'function') showFlashMessage("Please select a Deck Type.", "error");
            return;
        }

        let commanderId = null;
        let partnerId = null;
        let friendsForeverId = null;
        let doctorCompanionId = null;
        let timeLordDoctorId = null;
        let backgroundId = null;

        if (deckTypeId === COMMANDER_DECK_TYPE_ID) {
            if (!commanderInputElement || !commanderInputElement.dataset.commanderId) {
                if (typeof showFlashMessage === 'function') showFlashMessage("Please select a Commander.", "error");
                return;
            }
            commanderId = commanderInputElement.dataset.commanderId;
            if (partnerInputElement && partnerInputElement.dataset.partnerId) partnerId = partnerInputElement.dataset.partnerId;
            if (friendsForeverInputElement && friendsForeverInputElement.dataset.friendsForeverId) friendsForeverId = friendsForeverInputElement.dataset.friendsForeverId;
            if (doctorCompanionInputElement && doctorCompanionInputElement.dataset.timeLordDoctorId) timeLordDoctorId = doctorCompanionInputElement.dataset.timeLordDoctorId;
            if (timeLordDoctorInputElement && timeLordDoctorInputElement.dataset.doctorCompanionId) doctorCompanionId = timeLordDoctorInputElement.dataset.doctorCompanionId;
            if (backgroundInputElement && backgroundInputElement.dataset.backgroundId) backgroundId = backgroundInputElement.dataset.backgroundId;
        }

        const payload = {
            deck_name: deckName,
            deck_type: deckTypeId,
            commander_id: commanderId,
            partner_id: partnerId,
            friends_forever_id: friendsForeverId,
            doctor_companion_id: doctorCompanionId,
            time_lord_doctor_id: timeLordDoctorId,
            background_id: backgroundId
        };

        const selectedTagIds = deckTagInputInstance ? deckTagInputInstance.getSelectedTagIds() : [];

        try {
            const apiUrl = `/api/register_deck`;
            const response = await authFetch(apiUrl, {
                method: 'POST',
                body: JSON.stringify(payload)
            });
            if (!response) throw new Error("Authentication or network error occurred.");

            const data = await response.json();

            if (response.ok) {
                const newDeckId = data.deck?.id;
                let associationErrors = false;

                if (newDeckId && selectedTagIds.length > 0) {
                    const associationPromises = selectedTagIds.map(tagId => {
                        return authFetch(`/api/decks/${newDeckId}/tags`, {
                            method: 'POST',
                            body: JSON.stringify({ tag_id: tagId })
                        }).catch(err => {
                             console.error(`Error associating tag ${tagId} with deck ${newDeckId}:`, err);
                             associationErrors = true;
                             return null;
                        });
                    });
                    await Promise.all(associationPromises);
                }

                let finalMessage = data.message || `Deck "${deckName}" registered!`;
                if (associationErrors) {
                     finalMessage += " (Note: Some tags might not have been associated).";
                }
                sessionStorage.setItem("flashMessage", finalMessage);
                sessionStorage.setItem("flashType", associationErrors ? "warning" : "success");
                window.location.href = "/"; // Or trigger a refresh/update of the deck list

            } else {
                if (typeof showFlashMessage === 'function') showFlashMessage(data.error || `Error: ${response.statusText}`, "error");
            }
        } catch (error) {
             console.error("Error during deck registration fetch:", error);
             if (typeof showFlashMessage === 'function') showFlashMessage("An unexpected error occurred during registration.", "error");
        }
    });
});

// --- Exports ---
export { clearTagInput, initializeTagInput };