import { renderDeckCard, renderEmptyDecksMessage } from "./deckCardComponent.js";

function renderDecks(decks, containerElement) {
    if (!containerElement) {
        console.error("Render container not provided to renderDecks.");
        return;
    }
    containerElement.innerHTML = '';

    if (!decks || decks.length === 0) {
        renderEmptyDecksMessage(containerElement);
        return;
    }

    const fragment = document.createDocumentFragment();
    decks.forEach(deck => {
        const card = renderDeckCard(deck);
        fragment.appendChild(card);
    });
    containerElement.appendChild(fragment);
}

export function sortAndRenderDecks(decksToSort, sortOption, containerElement) {

    if (!containerElement) {
        console.error("Container element is required for sortAndRenderDecks.");
        return;
    }

    if (!decksToSort || !Array.isArray(decksToSort) || decksToSort.length === 0) {
        console.warn("sortAndRenderDecks called with invalid or empty decks data. Rendering empty message.");
        renderDecks([], containerElement);
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
    }

    renderDecks(sortedDecks, containerElement);
}