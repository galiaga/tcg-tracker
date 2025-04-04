export function renderDeckCard(deck) {
    const slug = deck.name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
    const card = document.createElement("a");
    card.href = `/decks/${deck.id}-${slug}`;
    card.className = "relative block rounded-xl shadow-md p-4 border hover:shadow-lg transition-all duration-200 ease-in-out cursor-pointer hover:scale-[1.02]";
    card.dataset.deckId = deck.id;

    const winrate = deck.win_rate ?? 0;
    card.classList.remove("bg-green-50", "border-green-200", "bg-yellow-50", "border-yellow-200", "bg-red-50", "border-red-200", "bg-white", "border-gray-200");

    if (winrate >= 60) {
        card.classList.add("bg-green-50", "border-green-200");
    } else if (winrate >= 40) {
        card.classList.add("bg-yellow-50", "border-yellow-200");
    } else if (deck.total_matches > 0) {
        card.classList.add("bg-red-50", "border-red-200");
    } else {
         card.classList.add("bg-white", "border-gray-200");
    }

    const formattedDate = formatDate(deck.last_match);
    const deckTypeName = deck.deck_type?.name ?? 'Unknown Format';

    let tagPillsHtml = '';
    if (deck.tags && deck.tags.length > 0) {
        tagPillsHtml = deck.tags.map(tag =>
            `<span class="tag-pill inline-flex items-center gap-1 bg-blue-100 text-blue-800 text-xs font-medium px-2 py-0.5 rounded-md mr-1 mb-1" data-tag-id="${tag.id}">
                ${tag.name}
                <button type="button" class="remove-tag-button ml-0.5 text-blue-500 hover:text-blue-700 font-bold focus:outline-none" aria-label="Remove tag ${tag.name}">&times;</button>
            </span>`
        ).join('');
    }

    const addTagButtonHtml = `
        <button type="button" class="add-deck-tag-button inline-flex items-center text-xs font-medium px-2 py-0.5 rounded border border-dashed border-gray-400 text-gray-500 hover:bg-gray-100 hover:text-gray-700 hover:border-solid mb-1" aria-label="Add tag to deck ${deck.name}" data-deck-id="${deck.id}">
            + Tag
        </button>
    `;

    const tagsContainerHtml = `<div class="mt-2 flex flex-wrap items-center gap-x-1">${tagPillsHtml}${addTagButtonHtml}</div>`;


    card.innerHTML = `
        <div class="flex items-start justify-between mb-2 gap-2">
            <h2 class="text-lg font-bold text-gray-800 min-w-0 break-words leading-tight flex-grow">${deck.name}</h2>
            <span class="text-xs bg-blue-500 text-white px-2 py-0.5 rounded-full font-medium whitespace-nowrap flex-shrink-0">
                ${deckTypeName}
            </span>
        </div>
        <div class="grid grid-cols-2 gap-x-4 gap-y-1 text-sm text-gray-600 mt-3">
            <div><span class="font-medium text-gray-700">Winrate:</span> ${winrate}%</div>
            <div><span class="font-medium text-gray-700">Matches:</span> ${deck.total_matches ?? 0}</div>
            <div><span class="font-medium text-gray-700">Wins:</span> ${deck.total_wins ?? 0}</div>
            <div><span class="font-medium text-gray-700">Last Match:</span> ${formattedDate}</div>
        </div>
        ${tagsContainerHtml}
    `;

    return card;
}

function formatDate(isoString) {
    if (!isoString) return "—";
    const date = new Date(isoString);
    if (isNaN(date.getTime())) return "—";
    const options = { month: "short", day: "numeric", year: "numeric" };
    try {
        return date.toLocaleDateString(undefined, options);
    } catch (e) {
        console.warn("Error formatting date:", e);
        return "Invalid Date";
    }
}

export function renderEmptyDecksMessage(containerElement) {
    if (!containerElement) return;
    containerElement.innerHTML = `
        <div class="text-center text-gray-500 mt-8 p-4 text-base border border-dashed border-gray-300 rounded-lg md:col-span-2 xl:col-span-3">
            No decks yet. Click 'New Deck' to get started!
        </div>
    `;
     containerElement.className = "grid gap-4 md:grid-cols-2 xl:grid-cols-3";
}