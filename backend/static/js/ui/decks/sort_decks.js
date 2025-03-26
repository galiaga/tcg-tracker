document.addEventListener("DOMContentLoaded", function () {
    document.getElementById("sort_decks")
            .addEventListener('change', handleDeckSortChange);
});

function handleDeckSortChange(event) {
    const sortOption = event.target.value;
    sortAndRenderDecks(sortOption);
}

function sortAndRenderDecks(sortOption) {
    console.log("sortOption = ", sortOption)
    console.log("window.userDecks = ", window.userDecks)
    if (!window.userDecks || !Array.isArray(userDecks)) {
        showFlashMessage("Decks not loaded yet.", "warning");
        return;
    }

    switch (sortOption) {

        case "last_match":
            userDecks.sort((a, b) => new Date(b.last_match) - new Date(a.last_match));
            break;

        case "matches":
            userDecks.sort((a, b) => b.total_matches - a.total_matches);
            break;

        case "name":
            userDecks.sort((a, b) => a.name.localeCompare(b.name));
            break;

        case "winrate":
            userDecks.sort((a, b) => b.win_rate - a.win_rate);
            break;

        default:
            console.warn("Unknown sorting option:", sortOption);
            return;
    }

    renderDecks(userDecks);
}

function renderDecks(decks) {

    const decksContainer = document.getElementById('decks-container');
    decksContainer.innerHTML = '';

    const fragment = document.createDocumentFragment();

    userDecks.forEach(deck => {
        const card = document.createElement("a");
        const slug = deck.name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
        card.href = `/decks/${deck.id}-${slug}`;
        card.className = "block rounded-2xl shadow-md p-4 bg-white border border-gray-200 hover:shadow-lg transition duration-300 cursor-pointer";

        card.innerHTML = `
            <h2 class="text-xl font-semibold mb-2">${deck.name}</h2>
            <p class="text-sm text-gray-500 mb-1"><strong>Format:</strong> ${deck.deck_type.name}</p>
            <p class="text-sm text-gray-500 mb-1"><strong>Winrate:</strong> ${deck.win_rate ?? 0}%</p>
            <p class="text-sm text-gray-500 mb-1"><strong>Matches:</strong> ${deck.total_matches ?? 0}</p>
            <p class="text-sm text-gray-500 mb-1"><strong>Wins:</strong> ${deck.total_wins ?? 0}</p>
            <p class="text-sm text-gray-500"><strong>Last Match:</strong> ${deck.last_match ?? 0}</p>
        `;

        fragment.appendChild(card);
    });

    decksContainer.appendChild(fragment);

}