// backend/static/js/registerDeck.js

import { authFetch } from './auth/auth.js';
import { registerDeck, associateTagWithDeck } from './api/deck-api.js';

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
        const selectedDoctorCompanionId = doctorCompanionInputElement?.dataset.doctorCompanionId || null;
        const selectedTimeLordDoctorId = timeLordDoctorInputElement?.dataset.timeLordDoctorId || null;
        const backgroundId = backgroundInputElement?.dataset.backgroundId || null;

        let selectedTagIds = [];
        if (typeof formElement.getSelectedTagsForNewDeck === 'function') {
            selectedTagIds = formElement.getSelectedTagsForNewDeck();
        } else {
            console.warn("[registerDeck.js] Could not find getSelectedTagsForNewDeck function on the form. Tags will not be saved.");
        }

        const payload = {
            deck_name: deckName,
            commander_id: commanderId,
            tags: selectedTagIds // Pass the tag IDs directly in the payload
        };
        
        if (partnerId) payload.partner_id = partnerId;
        if (friendsForeverId) payload.friends_forever_id = friendsForeverId;
        if (selectedDoctorCompanionId) payload.time_lord_doctor_id = selectedDoctorCompanionId;
        if (selectedTimeLordDoctorId) payload.doctor_companion_id = selectedTimeLordDoctorId;
        if (backgroundId) payload.background_id = backgroundId;

        
        try {
            // The payload now contains everything, including tags.
            const registerResponse = await registerDeck(payload);
            const data = await registerResponse.json().catch(() => ({ error: `Non-JSON response: ${registerResponse.statusText}` }));

            if (registerResponse.ok) {
                const newDeckId = data.deck?.id;
                const finalMessage = data.message || `Deck "${deckName}" registered!`;
                sessionStorage.setItem("flashMessage", finalMessage);
                sessionStorage.setItem("flashType", "success"); 
                window.location.href = `/my-decks?new_deck_id=${newDeckId}`;
            } else {
                if (typeof showFlashMessage === 'function') showFlashMessage(data.error || `Error: ${registerResponse.statusText}`, "error");
            }
        } catch (error) {
             console.error("Error during deck registration process:", error);
             if (typeof showFlashMessage === 'function') showFlashMessage(`An unexpected error occurred: ${error.message || 'Unknown error'}`, "error");
        }
    });
});