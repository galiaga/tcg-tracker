function updatePageTitle(newTitle) {
    document.title = `TCG Tracker: ${newTitle}`;
}

document.addEventListener("DOMContentLoaded", async () => {
    const pathParts = window.location.pathname.split("/");
    const idSlug = pathParts[pathParts.length - 1];
    const deckId = parseInt(idSlug.split("-")[0]);

    try {
        const token = localStorage.getItem("access_token");
        if (!token) {
            showFlashMessage("You need to log in to see decks", "warning");
            return;
        }

        const response = await authFetch(`/api/decks/${deckId}`, {
            method: "GET",
            headers: {
                "Authorization": `Bearer ${token}`,
                "Content-Type": "application/json"
            }
        });

        if (!response.ok) {
            showFlashMessage("Error loading deck details", "danger");
            return;
        }

        const deck = await response.json();

        const container = document.getElementById("deck-details");
        container.innerHTML = `
            <h2 class="text-xl font-bold mb-1">${deck.name}</h2>
            <p><span class="font-semibold text-gray-700">Format:</span> ${deck.deck_type.name}</p>
            <p><span class="font-semibold text-gray-700">Winrate:</span> ${deck.win_rate}%</p>
            <p><span class="font-semibold text-gray-700">Matches:</span> ${deck.total_matches}</p>
            <p><span class="font-semibold text-gray-700">Wins:</span> ${deck.total_wins}</p>
            ${deck.commander_name ? `<p><span class="font-semibold text-gray-700">Commander:</span> ${deck.commander_name}</p>` : ""}
            ${deck.associated_commander_name ? `<p><span class="font-semibold text-gray-700">Associated Commander:</span> ${deck.associated_commander_name}</p>` : ""}
        `;
        
        updatePageTitle(deck.name);

    } catch (error) {
        console.error(error);
        showFlashMessage(error.message, "danger");
    }
});