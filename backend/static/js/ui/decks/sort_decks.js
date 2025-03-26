import { renderDeckCard, renderEmptyDecksMessage } from "./deckCardComponent.js";

document.addEventListener("DOMContentLoaded", function () {
    document.getElementById("sort_decks")
            .addEventListener('change', handleDeckSortChange);
});

function handleDeckSortChange(event) {
    const sortOption = event.target.value;
    sortAndRenderDecks(sortOption);
}

function sortAndRenderDecks(sortOption) {
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
        const card = renderDeckCard(deck);
        fragment.appendChild(card);
    });

    decksContainer.appendChild(fragment);

}