document.addEventListener("DOMContentLoaded", function () {
    loadUserDecks();
});

async function loadUserDecks() {
    const container = document.getElementById("decks-container");
    container.innerHTML = "";

    try {
        const token = localStorage.getItem("access_token");
        if (!token) {
            showFlashMessage("You need to log in to load decks", "warning");
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

        if (!response.ok) throw new Error("Error fetching user decks");

        let userDecks = await response.json();

        if (!Array.isArray(userDecks)) {
            console.warn("Unexpected response format:", userDecks);
            userDecks = [];
        }

        if (userDecks.length === 0) {
            container.innerHTML = `
                <div class="text-center text-gray-500 mt-4">
                    No decks yet. Start by creating one!
                </div>
            `;
            return;
        }

        const fragment = document.createDocumentFragment();

        userDecks.forEach(deck => {
            const card = document.createElement("div");

            card.className = "rounded-2xl shadow-md p-4 bg-white border border-gray-200 hover:shadow-lg transition duration-300";

            card.innerHTML = `
                <h2 class="text-xl font-semibold mb-2">${deck.name}</h2>
                <p class="text-sm text-gray-500 mb-1"><strong>Format:</strong> ${deck.deck_type.name}</p>
                <p class="text-sm text-gray-500 mb-1"><strong>Winrate:</strong> ${deck.win_rate ?? 0}%</p>
                <p class="text-sm text-gray-500 mb-1"><strong>Matches:</strong> ${deck.total_matches ?? 0}</p>
                <p class="text-sm text-gray-500"><strong>Wins:</strong> ${deck.total_wins ?? 0}</p>
            `;

            fragment.appendChild(card);
        });

        container.appendChild(fragment);

    } catch (error) {
        console.error(error);
        showFlashMessage(error.message, "danger");
    }
}
