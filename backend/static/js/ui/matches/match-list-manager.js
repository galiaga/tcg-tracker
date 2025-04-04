import { authFetch } from '../../auth/auth.js';
import { formatMatchResult } from '../../utils.js';

function getSelectedMatchTagIds() {
    const tagFilterSelect = document.getElementById("filter-match-tags-select");
    const selectedIds = [];
    if (!tagFilterSelect) return selectedIds;

    for (const option of tagFilterSelect.options) {
        if (option.selected) {
            if (option.value && option.value !== "") {
                 selectedIds.push(option.value);
            }
        }
    }
    return selectedIds;
}

async function updateMatchHistoryView() {
    const matchesListContainer = document.getElementById("matches-list-items");
    const noMatchesMessage = document.getElementById("no-matches-message-history");

    if (!matchesListContainer || !noMatchesMessage) {
        console.error("Required UI elements for match history rendering not found.");
        return;
    }

    matchesListContainer.innerHTML = '<div class="p-6 text-center text-gray-500">Loading match history...</div>';
    noMatchesMessage.classList.add('hidden');

    const selectedTagIds = getSelectedMatchTagIds();

    const params = new URLSearchParams();
    if (selectedTagIds.length > 0) {
        params.append('tags', selectedTagIds.join(','));
    }

    const apiUrl = `/api/matches_history?${params.toString()}`;

    try {
        const response = await authFetch(apiUrl);

        if (!response) {
            throw new Error("Authentication or network error.");
        }
         if (!response.ok) {
             let errorMsg = `Error loading match history: ${response.status}`;
             try { const errorData = await response.json(); errorMsg = errorData.error || errorMsg; } catch(e) {}
             throw new Error(errorMsg);
         }

        const userMatches = await response.json();

        if (!Array.isArray(userMatches)) {
             throw new Error("Received invalid data format from server.");
        }

        matchesListContainer.innerHTML = "";

        if (userMatches.length === 0) {
            noMatchesMessage.textContent = "No match history found for the selected filters.";
            noMatchesMessage.classList.remove('hidden');
            return;
        }

        noMatchesMessage.classList.add('hidden');

        const fragment = document.createDocumentFragment();
        const locale = navigator.language || 'en-US';
        const dateOptions = { dateStyle: 'medium', timeStyle: 'short' };

        userMatches.forEach(match => { 
            const card = document.createElement("div");
            card.className = `bg-white shadow-md rounded-xl border border-gray-200 p-4 hover:shadow-lg transition-shadow duration-200`;

            const resultText = formatMatchResult(match.result);
            const lowerResult = resultText.toLowerCase();

            let badgeBgColorClass = 'bg-gray-400';
            let badgeTextColorClass = 'text-gray-800';

            if (lowerResult === 'win') {
                badgeBgColorClass = 'bg-green-500';
                badgeTextColorClass = 'text-white';
            } else if (lowerResult === 'loss') {
                badgeBgColorClass = 'bg-red-500';
                 badgeTextColorClass = 'text-white';
            } else if (lowerResult === 'draw') {
                badgeBgColorClass = 'bg-yellow-400';
                 badgeTextColorClass = 'text-gray-800';
            }

            let formattedDate = 'N/A';
             if (match.date) {
                 try {
                     formattedDate = new Date(match.date).toLocaleString(locale, dateOptions);
                 } catch(e) {
                     console.warn(`Could not format date: ${match.date}`, e);
                     formattedDate = match.date;
                 }
             }

             const deckName = match.deck?.name ?? 'N/A';
             const deckTypeName = match.deck_type?.name ?? 'N/A';

             let tagsHtml = '';
             if (match.tags && match.tags.length > 0) {
                 const tagPills = match.tags.map(tag =>
                     `<span class="inline-block bg-gray-200 text-gray-700 text-xs font-medium px-2.5 py-0.5 rounded-full mr-1 mb-1">
                         ${tag.name}
                     </span>`
                 ).join('');
                 tagsHtml = `<div class="mt-3 pt-2 border-t border-gray-100 flex flex-wrap">${tagPills}</div>`;
             }

             card.innerHTML = `
                <div class="flex items-start justify-between gap-3">
                    <div class="flex-grow min-w-0">
                        <h3 class="text-lg font-bold text-gray-800 break-words leading-tight truncate">${deckName}</h3>
                        <p class="text-xs text-gray-500 mt-1">${formattedDate}</p>
                    </div>
                    <div class="flex flex-col items-end flex-shrink-0 space-y-1">
                        <span class="text-xs ${badgeTextColorClass} ${badgeBgColorClass} px-2 py-0.5 rounded-full font-medium whitespace-nowrap">
                            ${resultText}
                        </span>
                        <span class="text-xs bg-blue-500 text-white px-2 py-0.5 rounded-full font-medium whitespace-nowrap">
                            ${deckTypeName}
                        </span>
                    </div>
                </div>
                ${tagsHtml}
            `;

            fragment.appendChild(card);
        });

        matchesListContainer.appendChild(fragment);

    } catch (error) {
        console.error("Failed to fetch or render match history:", error);
        if (typeof showFlashMessage === 'function') {
             showFlashMessage(error.message || "An unexpected error occurred loading history.", "danger");
        }
        matchesListContainer.innerHTML = ""; 
        noMatchesMessage.textContent = "Could not load match history due to an error.";
        noMatchesMessage.classList.remove('hidden');
    }
}

export { updateMatchHistoryView };

document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById("matches-list-items")) {
        updateMatchHistoryView();
    }
});