const COMMANDER_DECK_TYPE_ID = "7";

document.addEventListener("DOMContentLoaded", function() {
    const registerForm = document.getElementById("register-deck-form");
    if (!registerForm) {
        console.error("Register deck form not found!");
        return;
    }

    registerForm.addEventListener("submit", async function(event) {
        event.preventDefault();

        const token = localStorage.getItem("access_token");
        if (!token) {
            // Assuming showFlashMessage exists and handles UI
            showFlashMessage("Authentication error. Please log in again.", "error");
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
            showFlashMessage("Please enter a Deck Name.", "error");
            return;
        }
        if (!deckTypeId) {
            showFlashMessage("Please select a Deck Type.", "error");
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
                 showFlashMessage("Please select a Commander.", "error");
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

        console.log("Sending Payload:", JSON.stringify(payload, null, 2)); // Keep temporarily for debugging if needed

        try {
            // Assuming authFetch exists and handles auth + fetch
            const response = await authFetch("/api/register_deck", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(payload)
            });

            if (!response) {
                 showFlashMessage("Network error or authFetch failed.", "error");
                 return;
            }

            const data = await response.json();

            if (response.ok) {
                sessionStorage.setItem("flashMessage", data.message || `Deck "${deckName}" registered!`);
                sessionStorage.setItem("flashType", "success");
                window.location.href = "/";
            } else {
                showFlashMessage(data.error || `Error: ${response.statusText}`, "error");
            }
        } catch (error) {
             console.error("Error during deck registration fetch:", error);
             showFlashMessage("An unexpected error occurred during registration.", "error");
        }
    });
});