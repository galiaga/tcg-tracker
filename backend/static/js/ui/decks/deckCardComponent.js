// backend/static/js/ui/decks/deckCardComponent.js
import { openQuickAddTagModal } from '../tag-utils.js';

export function renderDeckCard(deck, refreshCallback) {
    const card = document.createElement("div");
    card.className = `deck-card relative bg-white dark:bg-slate-800 shadow-lg rounded-lg p-4 flex flex-col space-y-3 border-l-4 hover:shadow-xl transition-shadow duration-200 ease-in-out cursor-pointer`;
    card.dataset.deckId = deck.id;
    card.dataset.deckSlug = (deck.name || `deck-${deck.id}`).toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");

    const winrate = parseFloat(deck.win_rate ?? 0);
    const totalMatches = parseInt(deck.total_matches ?? 0, 10);

    let borderColorClassString = 'border-gray-300 dark:border-gray-600'; // Default/Neutral as a string
    if (totalMatches > 0) {
        if (winrate >= 60) {
            borderColorClassString = 'border-green-500 dark:border-green-500';
        } else if (winrate >= 40) {
            borderColorClassString = 'border-yellow-500 dark:border-yellow-500';
        } else {
            borderColorClassString = 'border-red-500 dark:border-red-500';
        }
    }
    // --- CORRECTED WAY TO ADD MULTIPLE CLASSES ---
    card.classList.add(...borderColorClassString.split(' '));


    const formattedDate = formatDate(deck.last_match);
    const deckFormatName = deck.format_name || 'Commander';

    let tagPillsHtml = '';
    if (deck.tags && deck.tags.length > 0) {
        tagPillsHtml = deck.tags.map(tag =>
            `<span class="tag-pill inline-flex items-center whitespace-nowrap bg-violet-100 dark:bg-violet-700/60 px-2.5 py-1 text-xs font-semibold text-violet-700 dark:text-violet-200 rounded-full" data-tag-id="${tag.id}">
                <span>${tag.name}</span>
                <button type="button" class="remove-tag-button ml-1.5 -mr-0.5 flex-shrink-0 rounded-full p-0.5 text-violet-500 dark:text-violet-400 hover:bg-violet-200 dark:hover:bg-violet-600 focus:outline-none focus:ring-1 focus:ring-violet-400 dark:focus:ring-violet-500" aria-label="Remove ${tag.name}">
                    <svg class="h-2.5 w-2.5" stroke="currentColor" fill="none" viewBox="0 0 8 8"><path stroke-linecap="round" stroke-width="1.5" d="M1 1l6 6m0-6L1 7" /></svg>
                </button>
            </span>`
        ).join('');
    }

    const addTagButtonHtml = `
        <button type="button" class="add-deck-tag-button text-xs font-medium text-violet-600 dark:text-violet-400 hover:text-violet-800 dark:hover:text-violet-200 border border-dashed border-violet-400 dark:border-violet-500 rounded-full px-2.5 py-1 hover:bg-violet-100 dark:hover:bg-violet-700/30 transition-colors leading-tight focus:outline-none focus:ring-1 focus:ring-violet-500" aria-label="Add tag to deck ${deck.name}" data-deck-id="${deck.id}">
            + Tag
        </button>
    `;

    card.innerHTML = `
        <div class="flex justify-between items-start gap-2">
            <div>
                <h2 class="text-lg font-semibold text-gray-900 dark:text-white leading-tight truncate" title="${deck.name || 'Unnamed Deck'}">${deck.name || 'Unnamed Deck'}</h2>
            </div>
            <span class="flex-shrink-0 text-xs bg-violet-600 text-white px-2.5 py-1 rounded-full font-semibold whitespace-nowrap">
                ${deckFormatName}
            </span>
        </div>

        <div class="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
            <div>
                <p class="text-gray-600 dark:text-gray-400">Win Rate: <span class="font-medium text-gray-800 dark:text-gray-200">${winrate.toFixed(2)}%</span></p>
                <p class="text-gray-600 dark:text-gray-400">Wins: <span class="font-medium text-gray-800 dark:text-gray-200">${deck.total_wins ?? 0}</span></p>
            </div>
            <div>
                <p class="text-gray-600 dark:text-gray-400">Matches: <span class="font-medium text-gray-800 dark:text-gray-200">${totalMatches}</span></p>
                <p class="text-gray-600 dark:text-gray-400">Last Played: <span class="font-medium text-gray-800 dark:text-gray-200">${formattedDate}</span></p>
            </div>
        </div>
        
        <div class="border-t border-gray-200 dark:border-gray-700/50 pt-3 mt-auto">
            <div class="tags-interactive-area flex flex-wrap items-center gap-1.5 min-h-[28px]">
                ${tagPillsHtml}
                ${addTagButtonHtml}
            </div>
        </div>
    `;

    const addTagButton = card.querySelector('.add-deck-tag-button');
    if (addTagButton) {
        addTagButton.addEventListener('click', (event) => {
            event.stopPropagation();
            event.preventDefault();
            const deckId = card.dataset.deckId;
            if (deckId && typeof refreshCallback === 'function') {
                openQuickAddTagModal(deckId, 'deck', refreshCallback);
            } else {
                console.error("Cannot open add tag modal: deckId missing or refreshCallback not provided for deck card.");
            }
        });
    }
    
    card.addEventListener('click', (event) => {
        if (event.target.closest('button')) {
            return;
        }
        const deckId = card.dataset.deckId;
        const slug = card.dataset.deckSlug;
        if (deckId && slug) {
            window.location.href = `/decks/${deckId}-${slug}`;
        } else if (deckId) {
            window.location.href = `/decks/${deckId}`;
        }
    });

    return card;
}

function formatDate(isoString) {
    if (!isoString) return "—";
    const date = new Date(isoString);
    if (isNaN(date.getTime())) return "—";
    const options = { day: 'numeric', month: 'short', year: 'numeric' };
    try {
        return date.toLocaleDateString('en-GB', options);
    } catch (e) {
        console.warn("Error formatting date:", e);
        return "Invalid Date";
    }
}

export function renderEmptyDecksMessage(containerElement, message = "No decks found. Create a deck to get started!") {
    if (!containerElement) return;
    containerElement.innerHTML = `
        <div class="text-center text-violet-700 dark:text-violet-300 mt-4 p-6 text-base border border-dashed border-violet-300 dark:border-violet-600 rounded-lg md:col-span-2 xl:col-span-3">
            ${message}
        </div>
    `;
     containerElement.className = "grid gap-4 md:grid-cols-2 xl:grid-cols-3";
}