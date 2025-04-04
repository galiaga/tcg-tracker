import { authFetch } from './auth/auth.js';
import { TagInputManager } from './ui/tagInput.js'; 

const COMMANDER_DECK_TYPE_ID = "7";

document.addEventListener("DOMContentLoaded", function() {
    const registerForm = document.getElementById("register-deck-form");
    if (!registerForm) {
        console.error("Register deck form not found!");
        return;
    }

    let deckTagInputInstance = null;
    const openModalBtn = document.getElementById('newDeckModalButton');
    const modal = document.getElementById('newDeckModal');
    const closeModalBtn = document.getElementById('newDeckModalCloseButton');

    function initializeTagInput() {
        if (typeof TagInputManager !== 'undefined') {
            deckTagInputInstance = TagInputManager.init({
                inputId: 'deck-tags-input',
                suggestionsId: 'deck-tags-suggestions',
                containerId: 'deck-tags-container'
            });
            if (deckTagInputInstance) {
                deckTagInputInstance.clearTags();
            } else {
                 console.error("Failed to initialize TagInputManager for decks.");
            }
        } else {
             console.warn("TagInputManager not loaded before registerDeck.js attempted init.");
        }
    }

    function clearTagInput() {
         if (deckTagInputInstance) {
             deckTagInputInstance.clearTags();
         }
    }

    if (openModalBtn) {
        openModalBtn.addEventListener('click', initializeTagInput);
    } else {
        console.warn("Button 'newDeckModalButton' not found for tag input init binding.");
    }

     if(closeModalBtn) {
         closeModalBtn.addEventListener('click', clearTagInput);
     }
     if(modal) {
        modal.addEventListener('click', (event) => {
           if (event.target === modal) {
               clearTagInput();
           }
        });
     }

    registerForm.addEventListener("submit", async function(event) {
        event.preventDefault();

        const token = localStorage.getItem("access_token");
        if (!token) {
            if (typeof showFlashMessage === 'function') {
                showFlashMessage("Authentication error. Please log in again.", "error");
            }
            return;
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

            if (partnerInputElement && partnerInputElement.dataset.partnerId) {
                partnerId = partnerInputElement.dataset.partnerId;
            }
            if (friendsForeverInputElement && friendsForeverInputElement.dataset.friendsForeverId) {
                friendsForeverId = friendsForeverInputElement.dataset.friendsForeverId;
            }
            if (doctorCompanionInputElement && doctorCompanionInputElement.dataset.timeLordDoctorId) {
                timeLordDoctorId = doctorCompanionInputElement.dataset.timeLordDoctorId;
            }
            if (timeLordDoctorInputElement && timeLordDoctorInputElement.dataset.doctorCompanionId) {
                 doctorCompanionId = timeLordDoctorInputElement.dataset.doctorCompanionId;
            }
            if (backgroundInputElement && backgroundInputElement.dataset.backgroundId) {
                 backgroundId = backgroundInputElement.dataset.backgroundId;
            }
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
            const response = await authFetch("/api/register_deck", {
                method: "POST",
                body: JSON.stringify(payload)
            });

            if (!response) {
                if (typeof showFlashMessage === 'function') showFlashMessage("Network error or authFetch failed.", "error");
                return;
            }

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
                     finalMessage += " (Note: Some tags might not have been associated due to errors - check console).";
                }
                sessionStorage.setItem("flashMessage", finalMessage);
                sessionStorage.setItem("flashType", associationErrors ? "warning" : "success");
                window.location.href = "/";

            } else {
                if (typeof showFlashMessage === 'function') showFlashMessage(data.error || `Error: ${response.statusText}`, "error");
            }
        } catch (error) {
             console.error("Error during deck registration fetch:", error);
             if (typeof showFlashMessage === 'function') showFlashMessage("An unexpected error occurred during registration.", "error");
        }
    });
});