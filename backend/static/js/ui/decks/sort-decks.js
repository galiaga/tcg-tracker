// backend/static/js/ui/decks/sort-decks.js
import { renderDeckCard, renderEmptyDecksMessage } from "./deckCardComponent.js";

// Updated to accept and pass refreshCallback
function renderDecks(decks, containerElement, refreshCallback) {
    if (!containerElement) {
        console.error("Render container not provided to renderDecks.");
        return;
    }
    containerElement.innerHTML = ''; // Clear previous content

    if (!decks || decks.length === 0) {
        renderEmptyDecksMessage(containerElement); // renderEmptyDecksMessage doesn't need refreshCallback
        return;
    }

    const fragment = document.createDocumentFragment();
    decks.forEach(deck => {
        // Pass the refreshCallback to renderDeckCard
        const card = renderDeckCard(deck, refreshCallback); 
        fragment.appendChild(card);
    });
    containerElement.appendChild(fragment);
}

// Updated to accept and pass refreshCallback
export function sortAndRenderDecks(decksToSort, sortOption, containerElement, refreshCallback) {

    if (!containerElement) {
        console.error("Container element is required for sortAndRenderDecks.");
        return;
    }

    // Ensure decksToSort is an array, even if empty
    const decksArray = Array.isArray(decksToSort) ? decksToSort : [];

    if (decksArray.length === 0) {
        // Pass refreshCallback, though renderDecks won't use it if decksArray is empty
        renderDecks([], containerElement, refreshCallback); 
        return;
    }

    const sortedDecks = [...decksArray]; // Work with a copy

    switch (sortOption) {
        case "last_match":
            sortedDecks.sort((a, b) => {
                // Handle null or invalid dates gracefully by treating them as very old
                const dateA = a.last_match && !isNaN(new Date(a.last_match)) ? new Date(a.last_match) : new Date(0);
                const dateB = b.last_match && !isNaN(new Date(b.last_match)) ? new Date(b.last_match) : new Date(0);
                return dateB - dateA; // Sorts more recent dates first
            });
            break;
        case "matches":
            sortedDecks.sort((a, b) => (b.total_matches ?? 0) - (a.total_matches ?? 0));
            break;
        case "name":
            sortedDecks.sort((a, b) => (a.name ?? '').localeCompare(b.name ?? ''));
            break;
        case "winrate":
            // Ensure win_rate is treated as a number
            sortedDecks.sort((a, b) => (parseFloat(b.win_rate) || 0) - (parseFloat(a.win_rate) || 0));
            break;
        case "creation_date": // Assuming your backend provides 'creation_date' or 'created_at'
            sortedDecks.sort((a, b) => {
                const dateA = a.creation_date && !isNaN(new Date(a.creation_date)) ? new Date(a.creation_date) : new Date(0);
                const dateB = b.creation_date && !isNaN(new Date(b.creation_date)) ? new Date(b.creation_date) : new Date(0);
                return dateB - dateA;
            });
            break;
        default:
            console.warn(`Unknown sort option: ${sortOption}. Decks will not be re-sorted.`);
            // Optionally, apply a default sort or leave as is
            break;
    }

    // Pass the refreshCallback to renderDecks
    renderDecks(sortedDecks, containerElement, refreshCallback);
}