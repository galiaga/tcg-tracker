import { renderDeckCard, renderEmptyDecksMessage } from "../ui/decks/deckCardComponent.js";
import { sortAndRenderDecks } from "../ui/decks/sort_decks.js";

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

        window.userDecks = await response.json();
        sortAndRenderDecks("last_match");

        if (!Array.isArray(userDecks)) {
            console.warn("Unexpected response format:", userDecks);
            userDecks = [];
        }

        if (userDecks.length === 0) {
            renderEmptyDecksMessage(container);
            return;
        }

    } catch (error) {
        console.error(error);
        showFlashMessage(error.message, "danger");
    }
}
