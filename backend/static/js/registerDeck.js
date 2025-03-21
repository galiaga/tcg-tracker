const COMMANDER_ID = "7";

document.addEventListener("DOMContentLoaded", function() {
    document.getElementById("register-deck-form").addEventListener("submit", async function(event) {
        event.preventDefault();

        const token = localStorage.getItem("access_token");
        const deckTypeId = document.getElementById("deck_type").value;
        const deckName = document.getElementById("deck_name").value;
        const commanderInput = document.getElementById("commander_name");
        const partnerInput = document.getElementById("partner_name");
        const friendsForeverInput = document.getElementById("friendsForever_name");
        const doctorCompanionInput = document.getElementById("doctorCompanion_name");
        const timeLordDoctorInput = document.getElementById("timeLordDoctor_name");

        const commanderId = deckTypeId === COMMANDER_ID ? commanderInput.dataset.commanderId : null;
        let partnerId = deckTypeId === COMMANDER_ID && partnerInput ? partnerInput.dataset.partnerId : null;

        // ✅ DEBUG: Imprimir valores antes de enviar el formulario
        console.log("Commander ID:", commanderId);
        console.log("Partner ID:", partnerId);

        // ✅ Si `partnerInput` tiene valor en el campo, pero `dataset.partnerId` es null, actualizarlo
        if (deckTypeId === "7" && partnerInput && partnerInput.value.trim() !== "" && !partnerId) {
            console.warn("⚠ Partner name is selected but partnerId is missing in dataset. Updating...");
            partnerId = await fetchPartnerId(partnerInput.value.trim());
            console.log("Updated Partner ID:", partnerId);
        }

        // ✅ Validación en el frontend: Si commander requiere partner y no se eligió, mostrar error
        if (deckTypeId === "7" && commanderInput.dataset.requiresPartner === "true" && !partnerId) {
            showFlashMessage("You must select a Partner for this Commander.", "error");
            return;
        }

        let friendsForeverId = deckTypeId === COMMANDER_ID && friendsForeverInput ? friendsForeverInput.dataset.friendsForeverId : null;
        let doctorCompanionId = deckTypeId === COMMANDER_ID && doctorCompanionInput ? doctorCompanionInput.dataset.doctorCompanionId : null;
        let timeLordDoctorId  = deckTypeId === COMMANDER_ID && timeLordDoctorInput ? timeLordDoctorInput.dataset.timeLordDoctorId : null;

        const response = await authFetch("/api/register_deck", {
            method: "POST",
            headers: {
                "Authorization": `Bearer ${token}`,
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ 
                deck_name: deckName,  
                deck_type: deckTypeId,
                commander_id: commanderId,
                partner_id: partnerId,
                friends_forever_id: friendsForeverId,
                doctor_companion_id: doctorCompanionId,
                time_lord_doctor_id: timeLordDoctorId
            })
        });

        if (!response) return;
        
        const data = await response.json();

        if (response.ok) {
            sessionStorage.setItem("flashMessage", `Deck "${deckName}" registered!`);
            sessionStorage.setItem("flashType", "success");
            window.location.href = "/";
        } else {
            showFlashMessage(data.error, "error");
        }
    });
});

// ✅ Función para obtener `partnerId` si el usuario ingresó solo el nombre
async function fetchPartnerId(partnerName) {
    try {
        const response = await fetch(`/api/search_commanders?q=${partnerName}&type=partner`);
        const commanders = await response.json();
        if (commanders.length > 0) {
            return commanders[0].id;  // Tomamos el primer resultado
        }
    } catch (error) {
        console.error("Error fetching partner ID:", error);
    }
    return null;
}