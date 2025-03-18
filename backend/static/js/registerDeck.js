document.addEventListener("DOMContentLoaded", function() {
    document.getElementById("register-deck-form").addEventListener("submit", async function(event) {
        event.preventDefault();

        const token = localStorage.getItem("access_token");
        const select = document.getElementById("deck_type");
        const deckTypeId = select.value;
        const deckName = document.getElementById("deck_name").value;
        const commanderInput = document.getElementById("commander_name");

        const commanderId = deckTypeId === "7" ? commanderInput.dataset.commanderId : null;

        const response = await authFetch("/api/register_deck", {
            method: "POST",
            headers: {
                "Authorization": `Bearer ${token}`,
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ 
                deck_name: deckName,  
                deck_type: deckTypeId,
                commander_id: commanderId
            })
        });

        if (!response) return;
        
        const data = await response.json();

        if (response.ok) {
            sessionStorage.setItem("flashMessage", "Deck " + deckName + " registered!");
            sessionStorage.setItem("flashType", "success");
            window.location.href = "/";
        } else {
            showFlashMessage(data.error, "error");
        }
    });
});
