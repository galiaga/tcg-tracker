document.addEventListener("DOMContentLoaded", function () {
    loadUserMatches();
});

async function loadUserMatches() {
    const table = document.getElementById("matches-list");
    const tbody = table.querySelector("tbody");

    tbody.innerHTML = "";

    try {
        const token = localStorage.getItem("access_token");
        if (!token) {
            showFlashMessage("You need to log in to load deck types", "warning");
            return;
        }

        const response = await authFetch("/api/matches_history", {
            method: "GET",
            headers: {
                "Authorization": `Bearer ${token}`,
                "Content-Type": "application/json"
            }
        });

        if (!response) return;

        if (!response.ok) throw new Error("Error fetching match history");

        const userMatches = await response.json();

        if (!Array.isArray(userMatches)) {
            console.warn("Unexpected response format:", userMatches);
            userMatches = [];
        }

        if (userMatches.length === 0) {
            tbody.innerHTML = `<tr><td colspan="2">No matches yet</td></tr>`;
            return;
        }

        const fragment = document.createDocumentFragment();
        
        userMatches.forEach(match => {
            const row = document.createElement("tr");

            row.innerHTML = `
                <td>${match.deck.name}</td>
                <td>${match.deck_type.name}</td>
                `;
            
                fragment.appendChild(row);
        });

        tbody.appendChild(fragment);

    } catch (error) {
        showFlashMessage(error.message, "danger");
    }
}