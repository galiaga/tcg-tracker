import { renderDeckCard, renderEmptyDecksMessage } from "./deckCardComponent.js";
import { updateDeckListView } from "./deck-list-manager.js";

document.addEventListener("DOMContentLoaded", function () {
    const sortSelect = document.getElementById("sort_decks");
    if (sortSelect) {
        sortSelect.addEventListener('change', updateDeckListView); 
    }
});

export function sortAndRenderDecks(decksToSort, sortOption) {
    console.log(`sortAndRenderDecks RECEIVED:`, decksToSort, `Is Array: ${Array.isArray(decksToSort)}`, `Sort Option: ${sortOption}`);

    if (!decksToSort || !Array.isArray(decksToSort)) {
        console.warn("sortAndRenderDecks called with invalid decks data.");
         const decksContainer = document.getElementById('decks-container');
         if(decksContainer) renderEmptyDecksMessage(decksContainer);
        return;
    }

    const sortedDecks = [...decksToSort];

    switch (sortOption) {
        case "last_match":
            sortedDecks.sort((a, b) => {
                const dateA = a.last_match ? new Date(a.last_match) : new Date(0);
                const dateB = b.last_match ? new Date(b.last_match) : new Date(0);
                return dateB - dateA;
            });
            break;
        case "matches":
            sortedDecks.sort((a, b) => (b.total_matches ?? 0) - (a.total_matches ?? 0));
            break;
        case "name":
            sortedDecks.sort((a, b) => (a.name ?? '').localeCompare(b.name ?? ''));
            break;
        case "winrate":
            sortedDecks.sort((a, b) => (b.win_rate ?? 0) - (a.win_rate ?? 0));
            break;
        case "creation_date":
            sortedDecks.sort((a, b) => {
                const dateA = a.creation_date ? new Date(a.creation_date) : new Date(0);
                const dateB = b.creation_date ? new Date(b.creation_date) : new Date(0);
                return dateB - dateA;
            });
            break;
        default:
            console.warn("Unknown sorting option:", sortOption);
            renderDecks(sortedDecks);
            return;
    }

    renderDecks(sortedDecks);
}

function renderDecks(decks) {
    const decksContainer = document.getElementById('decks-container');
    if (!decksContainer) {
        console.error("Decks container not found.");
        return;
    }
    decksContainer.innerHTML = '';

    if (decks.length === 0) {
        renderEmptyDecksMessage(decksContainer);
        return;
    }

    const fragment = document.createDocumentFragment();
    decks.forEach(deck => {
        const card = renderDeckCard(deck);
        fragment.appendChild(card);
    });
    decksContainer.appendChild(fragment);
}