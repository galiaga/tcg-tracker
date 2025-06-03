// backend/static/js/registerDeck.js
import { authFetch } from './auth/auth.js';
import { registerDeck, associateTagWithDeck } from './api/deck-api.js';
// FIELD_CONFIG is not directly imported here. We rely on dataset attributes being correctly set by deck-form.js.

const COMMANDER_DECK_TYPE_ID = "7"; // For Commander

document.addEventListener("DOMContentLoaded", function() {
    const registerForm = document.getElementById("register-deck-form");
    if (!registerForm) {
        console.warn("[registerDeck.js] Deck registration form #register-deck-form not found.");
        return;
    }

    registerForm.addEventListener("submit", async function(event) {
        event.preventDefault();
        const formElement = event.target;

        const deckNameElement = formElement.querySelector("#deck_name");
        const commanderInputElement = formElement.querySelector("#commander_name");
        const partnerInputElement = formElement.querySelector("#partner_name");
        const friendsForeverInputElement = formElement.querySelector("#friendsForever_name");
        const doctorCompanionInputElement = formElement.querySelector("#doctorCompanion_name"); // Input for selecting a Doctor's Companion
        const timeLordDoctorInputElement = formElement.querySelector("#timeLordDoctor_name");   // Input for selecting a Time Lord Doctor
        const backgroundInputElement = formElement.querySelector("#chooseABackground_name");

        const deckName = deckNameElement ? deckNameElement.value.trim() : "";
        const deckTypeId = COMMANDER_DECK_TYPE_ID;

        if (!deckName) {
            if (typeof showFlashMessage === 'function') showFlashMessage("Please enter a Deck Name.", "error");
            return;
        }

        const commanderId = commanderInputElement?.dataset.commanderId || null;
        if (!commanderId && commanderInputElement && commanderInputElement.offsetParent !== null) {
             if (typeof showFlashMessage === 'function') showFlashMessage("Please select a Commander.", "error");
             return;
        }
        
        const partnerId = partnerInputElement?.dataset.partnerId || null;
        const friendsForeverId = friendsForeverInputElement?.dataset.friendsForeverId || null;
        // These will read the dataset attributes set by deck-form.js using the corrected FIELD_CONFIG
        const selectedDoctorCompanionId = doctorCompanionInputElement?.dataset.doctorCompanionId || null;
        const selectedTimeLordDoctorId = timeLordDoctorInputElement?.dataset.timeLordDoctorId || null;
        const backgroundId = backgroundInputElement?.dataset.backgroundId || null;

        const tagInstance = formElement.tagInputInstance;
        const selectedTagIds = tagInstance ? tagInstance.getSelectedTagIds() : [];

        const payload = {
            deck_name: deckName,
            deck_type: deckTypeId,
            commander_id: commanderId
        };
        
        if (partnerId) payload.partner_id = partnerId;
        if (friendsForeverId) payload.friends_forever_id = friendsForeverId;
        // Assign to the correct payload keys that the backend expects
        if (selectedDoctorCompanionId) payload.time_lord_doctor_id = selectedDoctorCompanionId;
        if (selectedTimeLordDoctorId) payload.doctor_companion_id = selectedTimeLordDoctorId;
        if (backgroundId) payload.background_id = backgroundId;

        
        try {
            const registerResponse = await registerDeck(payload);
            const data = await registerResponse.json().catch(() => ({ error: `Non-JSON response: ${registerResponse.statusText}` }));

            if (registerResponse.ok) {
                const newDeckId = data.deck?.id;
                let associationErrors = false;
                if (newDeckId && selectedTagIds.length > 0) {
                    const associationPromises = selectedTagIds.map(async (tagId) => {
                        try {
                            const assocResponse = await associateTagWithDeck(newDeckId, tagId);
                            if (!assocResponse.ok) {
                                console.error(`Error associating tag ${tagId} with deck ${newDeckId}: Status ${assocResponse.status}`);
                                associationErrors = true;
                            }
                        } catch (err) {
                             console.error(`Network/Auth error associating tag ${tagId} with deck ${newDeckId}:`, err);
                             associationErrors = true;
                        }
                    });
                    await Promise.all(associationPromises);
                }

                let finalMessage = data.message || `Deck "${deckName}" registered!`;
                if (associationErrors) {
                     finalMessage += " (Note: Some tags might not have been associated).";
                }
                sessionStorage.setItem("flashMessage", finalMessage);
                sessionStorage.setItem("flashType", associationErrors ? "warning" : "success");
                window.location.href = "/my-decks";
            } else {
                if (typeof showFlashMessage === 'function') showFlashMessage(data.error || `Error: ${registerResponse.statusText}`, "error");
            }
        } catch (error) {
             console.error("Error during deck registration process:", error);
             if (typeof showFlashMessage === 'function') showFlashMessage(`An unexpected error occurred: ${error.message || 'Unknown error'}`, "error");
        }
    });
});