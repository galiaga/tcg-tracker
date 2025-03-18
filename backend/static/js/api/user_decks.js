document.addEventListener("DOMContentLoaded", function () {
    loadUserDecks();
});

async function loadUserDecks() {
    const table = document.getElementById("decks-list");
    const tbody = table.querySelector("tbody");

    tbody.innerHTML = "";

    try {
        const token = localStorage.getItem("access_token");
        if (!token) {
            showFlashMessage("You need to log in to load deck types", "warning");
            return;
        }

        const response = await authFetch("/api/user_decks", {
            method: "GET",
            headers: {
                "Authorization": `Bearer ${token}`,
                "Content-Type": "application/json"
            }
        });

        if (!response) return;

        if (!response.ok) throw new Error("Error fetching match history");

        const userDecks = await response.json();

        if (!Array.isArray(userDecks)) {
            console.warn("Unexpected response format:", userDecks);
            userDecks = [];
        }
        
        if (userDecks.length === 0) {
            tbody.innerHTML = `<tr><td colspan="2">No decks yet</td></tr>`;
            return;
        }

        const fragment = document.createDocumentFragment();

        userDecks.forEach(deck => {
            const row = document.createElement("tr");

            row.innerHTML = `
                <td>${deck.name}</td>
                <td>${deck.deck_type.name}</td>
                <td>${deck.win_rate ?? 0}</td>
                <td>${deck.total_matches ?? 0}</td>
                <td>${deck.total_wins ?? 0}</td>
                `;
            
                fragment.appendChild(row);
        });

        tbody.appendChild(fragment);

    } catch (error) {
        showFlashMessage(error.message, "danger");
    }
}