document.addEventListener("DOMContentLoaded", async function() {
    const token = localStorage.getItem("access_token");
    if (!token) {
        return;
    }

    const select = document.getElementById("deck-select");
    const form = document.getElementById("log-match-form");

    if (!select || !form) {
        console.warn("logMatch.js: No se encontraron elementos esperados en esta vista.");
        return;
    }
    
    try {
        // Load user decks
        const response = await authFetch("/api/user_decks", {
            method: "GET",
            headers: {
                "Authorization": `Bearer ${token}`,
                "Content-Type": "application/json"
            }
        });

        if (!response) return;

        if (!response.ok) {
            throw new Error(`Error: ${response.status}`);
        }

        const decks = await response.json();

        decks.forEach(deck => {
            const option = document.createElement("option");
            option.value = deck.id;
            option.dataset.name = deck.name;
            option.textContent = deck.name;
            select.appendChild(option);
        });

    } catch (error) {
        console.error("Failed to fetch decks:", error);
    }

    // Get match from user
    document.getElementById("log-match-form").addEventListener("submit", async function(event) {
        event.preventDefault();

        const selectedOption = select.options[select.selectedIndex];
        const deckId = select.value;
        
        if (!deckId || selectedOption.disabled) {
            showFlashMessage("Please select a valid deck before logging a match.", "error");
            return;
        }

        const deckName = selectedOption.dataset.name;
        const matchResult = document.querySelector('input[name="match_result"]:checked').value;
        const resultMapping = { "0": "Victory", "1": "Defeat", "2": "Draw" };
        const matchResultText = resultMapping[matchResult];

        const response = await authFetch("/api/log_match", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            },
            body: JSON.stringify({ deck_id: deckId, match_result: matchResult })
        });

        if (!response) return;
        
        const data = await response.json();

        if (response.ok) {
            sessionStorage.setItem("flashMessage", `${matchResultText} with ${deckName} registered!`);
            sessionStorage.setItem("flashType", "success");
            window.location.href = "/";
        } else {
            showFlashMessage(data.error, "error");
        }
});

});