import { authFetch } from './auth/auth.js';
// Import only the necessary API functions
import { registerDeck, associateTagWithDeck } from './api/deck-api.js';

// --- Configuration ---
const COMMANDER_DECK_TYPE_ID = "7"; // Consider importing this if defined elsewhere centrally

document.addEventListener("DOMContentLoaded", function() {
    const registerForm = document.getElementById("register-deck-form");
    if (!registerForm) return;

    // --- Form Submission Logic ---
    registerForm.addEventListener("submit", async function(event) {
        event.preventDefault();
        const formElement = event.target; // Get the form element

        // --- Data Gathering ---
        const deckTypeElement = formElement.querySelector("#deck_type");
        const deckNameElement = formElement.querySelector("#deck_name");
        const commanderInputElement = formElement.querySelector("#commander_name");
        const partnerInputElement = formElement.querySelector("#partner_name");
        const friendsForeverInputElement = formElement.querySelector("#friendsForever_name");
        const doctorCompanionInputElement = formElement.querySelector("#doctorCompanion_name"); // Check ID mapping
        const timeLordDoctorInputElement = formElement.querySelector("#timeLordDoctor_name"); // Check ID mapping
        const backgroundInputElement = formElement.querySelector("#chooseABackground_name");

        const deckTypeId = deckTypeElement ? deckTypeElement.value : null;
        const deckName = deckNameElement ? deckNameElement.value.trim() : "";

        // --- Basic Validation ---
        if (!deckName) {
            if (typeof showFlashMessage === 'function') showFlashMessage("Please enter a Deck Name.", "error");
            return;
        }
        if (!deckTypeId) {
            if (typeof showFlashMessage === 'function') showFlashMessage("Please select a Deck Type.", "error");
            return;
        }

        // --- Gather Commander/Partner IDs ---
        let commanderId = null;
        let partnerId = null;
        let friendsForeverId = null;
        let doctorCompanionId = null; // Check ID mapping
        let timeLordDoctorId = null; // Check ID mapping
        let backgroundId = null;

        if (deckTypeId === COMMANDER_DECK_TYPE_ID) {
            commanderId = commanderInputElement?.dataset.commanderid || null; // Use lowercase dataset key
            if (!commanderId) {
                 if (typeof showFlashMessage === 'function') showFlashMessage("Please select a Commander.", "error");
                 return;
            }
            partnerId = partnerInputElement?.dataset.partnerid || null;
            friendsForeverId = friendsForeverInputElement?.dataset.friendsforeverid || null;
            // Ensure correct dataset keys are used based on FIELD_CONFIG in deck-form.js
            timeLordDoctorId = doctorCompanionInputElement?.dataset.timelorddoctorid || null; // Key from FIELD_CONFIG
            doctorCompanionId = timeLordDoctorInputElement?.dataset.doctorcompanionid || null; // Key from FIELD_CONFIG
            backgroundId = backgroundInputElement?.dataset.backgroundid || null;
        }

        // --- Gather Tags ---
        const tagInstance = formElement.tagInputInstance; // Access instance attached by modal script
        const selectedTagIds = tagInstance ? tagInstance.getSelectedTagIds() : [];
        if (!tagInstance) {
             console.warn("TagInputManager instance not found on form during submit.");
             // Optionally inform user if tags are critical:
             // if (typeof showFlashMessage === 'function') showFlashMessage("Tag input error. Cannot get tags.", "error");
             // Depending on requirements, you might want to return here or proceed without tags.
        }

        // --- Prepare Payload ---
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

        // --- API Interaction ---
        try {
            // Register the deck
            const registerResponse = await registerDeck(payload);
            const data = await registerResponse.json(); // Need to parse JSON regardless of status

            if (registerResponse.ok) {
                const newDeckId = data.deck?.id;
                let associationErrors = false;

                // Associate tags if deck creation was successful and tags exist
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

                // --- Handle Success ---
                let finalMessage = data.message || `Deck "${deckName}" registered!`;
                if (associationErrors) {
                     finalMessage += " (Note: Some tags might not have been associated).";
                }
                sessionStorage.setItem("flashMessage", finalMessage);
                sessionStorage.setItem("flashType", associationErrors ? "warning" : "success");
                window.location.href = "/"; // Or trigger UI update

            } else {
                // --- Handle Registration Error ---
                if (typeof showFlashMessage === 'function') showFlashMessage(data.error || `Error: ${registerResponse.statusText}`, "error");
            }
        } catch (error) {
             // --- Handle Network/Auth Errors ---
             console.error("Error during deck registration process:", error);
             if (typeof showFlashMessage === 'function') showFlashMessage(`An unexpected error occurred: ${error.message || 'Unknown error'}`, "error");
        }
    });
});

// No exports needed from this file anymore regarding tags