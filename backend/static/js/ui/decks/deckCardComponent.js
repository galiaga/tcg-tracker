export function renderDeckCard(deck) {
    const slug = deck.name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
    const card = document.createElement("a");
    card.href = `/decks/${deck.id}-${slug}`;
    card.className = "block rounded-xl shadow-md p-4 border hover:shadow-lg transition-all duration-200 ease-in-out cursor-pointer hover:scale-[1.02]";

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

    let tagsHtml = '';
    if (deck.tags && deck.tags.length > 0) {
        const tagPills = deck.tags.map(tag =>
            `<span class="inline-block bg-gray-200 text-gray-700 text-xs font-medium px-2.5 py-0.5 rounded-full mr-1 mb-1">
                ${tag.name}
            </span>`
        ).join('');
        tagsHtml = `<div class="mt-3 pt-2 border-t border-gray-200 flex flex-wrap">${tagPills}</div>`;
    }

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
        ${tagsHtml}
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