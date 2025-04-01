import { sortAndRenderDecks } from '../decks/sort_decks.js';

document.addEventListener("DOMContentLoaded", function () {
    document.getElementById("filter_decks")
            .addEventListener('change', handleDeckFilterChange);
});

function handleDeckFilterChange(event) {
    const filterOption = event.target.value;
    filterAndRenderDecks(filterOption);
}

async function filterAndRenderDecks(filterOption) {
    if (!window.userDecks || !Array.isArray(userDecks)) {
        showFlashMessage("Decks not loaded yet.", "warning");
        return;
    }

    let apiUrl = '/api/user_decks';

    if (filterOption && filterOption.toLowerCase() !== '0') {
        apiUrl += `?deck_type_id=${encodeURIComponent(filterOption)}`;
    }

    try {
        const token = localStorage.getItem("access_token");
        if (!token) {
            showFlashMessage("You need to log in to see decks", "warning");
            return;
        }

        const response = await authFetch(apiUrl, {
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

        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }

        const filteredDecks = await response.json();
        window.userDecks = filteredDecks || [];

        const sortSelectElement = document.getElementById("sort_decks");
        const currentSortValue = sortSelectElement ? sortSelectElement.value : 'last_match';
        sortAndRenderDecks(currentSortValue);

    } catch (error) {
        console.error("Error fetching/rendering filtered decks:", error);
        const decksContainer = document.getElementById('decks-container');
        if (decksContainer) decksContainer.innerHTML = '<p class="text-red-500">Error loading filtered decks.</p>';
    }

};