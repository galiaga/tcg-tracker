// Corrected import: handleRemoveDeckTagClick instead of handleRemoveTagClick
import { openQuickAddTagModal, handleRemoveDeckTagClick } from '../tag-utils.js'; 

export function renderDeckCard(deck, refreshCallback) {
    const card = document.createElement("div");
    card.className = `deck-card relative bg-white dark:bg-slate-800 shadow-lg rounded-lg p-4 flex flex-col space-y-3 border-l-4 hover:shadow-xl transition-shadow duration-200 ease-in-out cursor-pointer`;
    card.dataset.deckId = deck.id;
    card.dataset.deckName = deck.name; 
    card.dataset.deckSlug = (deck.name || `deck-${deck.id}`).toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");

    const winrate = parseFloat(deck.win_rate ?? 0);
    const totalMatches = parseInt(deck.total_matches ?? 0, 10);

    let borderColorClassString = 'border-gray-300 dark:border-gray-600';
    if (totalMatches > 0) {
        if (winrate >= 60) {
            borderColorClassString = 'border-green-500 dark:border-green-500';
        } else if (winrate >= 40) {
            borderColorClassString = 'border-yellow-500 dark:border-yellow-500';
        } else {
            borderColorClassString = 'border-red-500 dark:border-red-500';
        }
    }
    card.classList.add(...borderColorClassString.split(' '));

    const formattedDate = formatDate(deck.last_match);

    let tagPillsHtml = '';
    if (deck.tags && deck.tags.length > 0) {
        tagPillsHtml = deck.tags.map(tag =>
            `<span class="tag-pill inline-flex items-center whitespace-nowrap bg-violet-100 dark:bg-violet-700/60 px-2.5 py-1 text-xs font-semibold text-violet-700 dark:text-violet-200 rounded-full" data-tag-id="${tag.id}" data-tag-name="${tag.name.replace(/"/g, '"')}">
                <span>${tag.name}</span>
                <button type="button" class="remove-deck-tag-button ml-1.5 -mr-0.5 flex-shrink-0 rounded-full p-0.5 text-violet-500 dark:text-violet-400 hover:bg-violet-200 dark:hover:bg-violet-600 focus:outline-none focus:ring-1 focus:ring-violet-400 dark:focus:ring-violet-500" aria-label="Remove ${tag.name}">
                    <svg class="h-2.5 w-2.5 pointer-events-none" stroke="currentColor" fill="none" viewBox="0 0 8 8"><path stroke-linecap="round" stroke-width="1.5" d="M1 1l6 6m0-6L1 7" /></svg>
                </button>
            </span>`
        ).join('');
    }

    const addTagButtonHtml = `
        <button type="button" class="add-deck-tag-button text-xs font-medium text-violet-600 dark:text-violet-400 hover:text-violet-800 dark:hover:text-violet-200 border border-dashed border-violet-400 dark:border-violet-500 rounded-full px-2.5 py-1 hover:bg-violet-100 dark:hover:bg-violet-700/30 transition-colors leading-tight focus:outline-none focus:ring-1 focus:ring-violet-500" aria-label="Add tag to deck ${deck.name}">
            + Tag
        </button>
    `;

    card.innerHTML = `
        <div class="flex justify-between items-start gap-2">
            <h2 class="text-xl font-bold text-gray-900 dark:text-white leading-tight truncate" title="${deck.name || 'Unnamed Deck'}">${deck.name || 'Unnamed Deck'}</h2>
            <div class="relative deck-card-actions flex-shrink-0">
                <button type="button" class="deck-card-options-btn p-1.5 rounded-full text-gray-400 dark:text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700 hover:text-gray-600 dark:hover:text-gray-300 focus:outline-none focus:ring-2 focus:ring-offset-1 dark:focus:ring-offset-slate-800 focus:ring-violet-500" aria-label="Deck options" aria-haspopup="true" aria-expanded="false">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5 pointer-events-none"><path stroke-linecap="round" stroke-linejoin="round" d="M12 6.75a.75.75 0 1 1 0-1.5.75.75 0 0 1 0 1.5ZM12 12.75a.75.75 0 1 1 0-1.5.75.75 0 0 1 0 1.5ZM12 18.75a.75.75 0 1 1 0-1.5.75.75 0 0 1 0 1.5Z" /></svg>
                </button>
                <div class="deck-card-action-menu hidden absolute right-0 mt-1 w-48 origin-top-right bg-white dark:bg-gray-700 rounded-md shadow-lg ring-1 ring-black dark:ring-gray-600 ring-opacity-5 focus:outline-none z-20" role="menu" aria-orientation="vertical">
                    <div class="py-1" role="none">
                        <button type="button" class="menu-view-details-btn text-gray-700 dark:text-gray-200 group flex items-center w-full px-4 py-2 text-sm text-left hover:bg-gray-100 dark:hover:bg-gray-600" role="menuitem">
                            <svg class="mr-3 h-5 w-5 text-gray-400 dark:text-gray-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M10 12.5a2.5 2.5 0 100-5 2.5 2.5 0 000 5z" /><path fill-rule="evenodd" d="M.664 10.59a1.651 1.651 0 010-1.18l.828-1.473a1.651 1.651 0 012.861-.404l.708.709a1.651 1.651 0 002.332 0l.708-.709a1.651 1.651 0 012.861.404l.828 1.473a1.651 1.651 0 010 1.18l-.828 1.473a1.651 1.651 0 01-2.861.404l-.708-.709a1.651 1.651 0 00-2.332 0l-.708.709a1.651 1.651 0 01-2.861-.404l-.828-1.473zM10 15a5 5 0 100-10 5 5 0 000 10z" clip-rule="evenodd" /></svg>
                            View Details
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <div class="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
            <div>
                <p class="text-gray-600 dark:text-gray-400">Win Rate: <span class="font-medium text-gray-800 dark:text-gray-200">${winrate.toFixed(1)}%</span></p>
                <p class="text-gray-600 dark:text-gray-400">Wins: <span class="font-medium text-gray-800 dark:text-gray-200">${deck.total_wins ?? 0}</span></p>
            </div>
            <div>
                <p class="text-gray-600 dark:text-gray-400">Matches: <span class="font-medium text-gray-800 dark:text-gray-200">${totalMatches}</span></p>
                <p class="text-gray-600 dark:text-gray-400">Last Played: <span class="font-medium text-gray-800 dark:text-gray-200">${formattedDate}</span></p>
            </div>
        </div>
        
        <div class="border-t border-gray-200 dark:border-gray-700/50 pt-2.5 mt-2.5">
            <div class="tags-interactive-area flex flex-wrap items-center gap-1.5 min-h-[26px]">
                ${tagPillsHtml}
                ${addTagButtonHtml}
            </div>
        </div>
    `;
    
    card.addEventListener('click', async (event) => {
        const addTagButtonTarget = event.target.closest('.add-deck-tag-button');
        const removeTagButtonTarget = event.target.closest('.remove-deck-tag-button');
        const optionsButtonTarget = event.target.closest('.deck-card-options-btn');
        const viewDetailsButtonTarget = event.target.closest('.menu-view-details-btn');

        const deckId = card.dataset.deckId;

        if (addTagButtonTarget) {
            event.stopPropagation();
            event.preventDefault();
            if (deckId && typeof refreshCallback === 'function') {
                openQuickAddTagModal(deckId, 'deck', refreshCallback);
            }
        } else if (removeTagButtonTarget) {
            event.stopPropagation();
            event.preventDefault();
            const tagPill = removeTagButtonTarget.closest('.tag-pill');
            const tagId = tagPill?.dataset.tagId;
            if (deckId && tagId && typeof refreshCallback === 'function') {
                // Use the correctly imported function name
                await handleRemoveDeckTagClick(deckId, tagId, refreshCallback, removeTagButtonTarget, tagPill);
            }
        } else if (optionsButtonTarget) {
            event.stopPropagation();
            const menu = card.querySelector('.deck-card-action-menu');
            if (menu) {
                menu.classList.toggle('hidden');
                optionsButtonTarget.setAttribute('aria-expanded', String(!menu.classList.contains('hidden')));
            }
        } else if (viewDetailsButtonTarget) {
            event.stopPropagation();
            navigateToDeckDetails(deckId, card.dataset.deckSlug);
        } else if (!event.target.closest('button') && !event.target.closest('.deck-card-action-menu')) {
            navigateToDeckDetails(deckId, card.dataset.deckSlug);
        }
    });
    
    document.addEventListener('click', (event) => {
        const menu = card.querySelector('.deck-card-action-menu');
        const optionsBtn = card.querySelector('.deck-card-options-btn');
        // Ensure menu and optionsBtn exist before trying to access properties or call methods
        if (menu && !menu.classList.contains('hidden') && 
            optionsBtn && !optionsBtn.contains(event.target) && 
            !menu.contains(event.target)) {
            menu.classList.add('hidden');
            optionsBtn.setAttribute('aria-expanded', 'false');
        }
    }, true);


    return card;
}

function navigateToDeckDetails(deckId, slug) {
    if (deckId && slug) {
        window.location.href = `/decks/${deckId}-${slug}`;
    } else if (deckId) {
        window.location.href = `/decks/${deckId}`;
    }
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