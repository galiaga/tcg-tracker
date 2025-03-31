export function renderDeckCard(deck) {
    const slug = deck.name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
    const card = document.createElement("a");
    card.href = `/decks/${deck.id}-${slug}`;
    card.className = "block rounded-2xl shadow-md p-4 border border-gray-200 hover:shadow-lg transition duration-300 cursor-pointer hover:scale-105";

    const winrate = deck.win_rate ?? 0;
    if (winrate >= 60) {
        card.classList.add("bg-green-100", "border-green-200");
    } else if (winrate >= 30) {
        card.classList.add("bg-yellow-50", "border-yellow-200");
    } else {
        card.classList.add("bg-red-100", "border-red-200");
    }

    const formattedDate = formatDate(deck.last_match);

    card.innerHTML = `
        <div class="flex items-start justify-between mb-2">
            <h2 class="text-lg font-bold text-gray-800 min-w-0 break-words md:truncate">${deck.name}</h2>
            <span class="text-xs bg-blue-500 text-white px-2 py-0.5 rounded-md font-medium whitespace-nowrap">
                ${deck.deck_type.name}
            </span>
        </div>

        <div class="grid grid-cols-2 gap-y-1 text-sm text-gray-600">
            <div><span class="font-semibold text-gray-700">Winrate:</span> ${winrate}%</div>
            <div><span class="font-semibold text-gray-700">Matches:</span> ${deck.total_matches ?? 0}</div>
            <div><span class="font-semibold text-gray-700">Wins:</span> ${deck.total_wins ?? 0}</div>
            <div><span class="font-semibold text-gray-700">Last Match:</span> ${formattedDate}</div>
        </div>
    `;

    return card;
}

function formatDate(isoString) {
    if (!isoString) return "—";
    const date = new Date(isoString);
    if (isNaN(date)) return "—";
    return date.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

export function renderEmptyDecksMessage(containerElement) {
    containerElement.innerHTML = `
        <div class="text-center text-gray-500 mt-4 text-sm">
            No decks yet. Start by creating one!
        </div>
    `;
}