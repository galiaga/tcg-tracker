import { formatMatchResult } from "../utils.js";
import { authFetch } from '../auth/auth.js';

document.addEventListener("DOMContentLoaded", loadUserMatches);

export async function loadUserMatches() {
    const matchesListContainer = document.getElementById("matches-list-items");
    const noMatchesMessage = document.getElementById("no-matches-message-history");
    const loadingMessage = matchesListContainer.querySelector('div');

    if (!matchesListContainer || !noMatchesMessage || !loadingMessage) {
        console.error("Required UI elements for match history list not found.");
        return;
    }

    noMatchesMessage.classList.add('hidden');
    loadingMessage.classList.remove('hidden');

    try {
        const token = localStorage.getItem("access_token");
        if (!token) {
            loadingMessage.textContent = "Please log in to view history.";
            loadingMessage.classList.remove('hidden');
            matchesListContainer.innerHTML = '';
            matchesListContainer.appendChild(loadingMessage);
            noMatchesMessage.classList.add('hidden');
            return;
        }

        const response = await authFetch("/api/matches_history", {
            method: "GET",
            headers: { "Authorization": `Bearer ${token}` }
        });

        if (!response.ok) {
            let errorMsg = `Error loading match history: ${response.status}`;
            try { const errorData = await response.json(); errorMsg = errorData.error || errorMsg; } catch(e) {}
            showFlashMessage(errorMsg, "danger");
            matchesListContainer.innerHTML = "";
            noMatchesMessage.textContent = "Could not load match history.";
            noMatchesMessage.classList.remove('hidden');
            return;
        }

        const userMatches = await response.json();

        if (!Array.isArray(userMatches)) {
            console.error("API response is not an array:", userMatches);
            throw new Error("Received invalid data format from server.");
        }

        matchesListContainer.innerHTML = "";

        if (userMatches.length === 0) {
            noMatchesMessage.textContent = "No match history found.";
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
            `;

            fragment.appendChild(card);
        });

        matchesListContainer.appendChild(fragment);

    } catch (error) {
        console.error("Failed to fetch or render match history:", error);
        showFlashMessage(error.message || "An unexpected error occurred loading history.", "danger");
        matchesListContainer.innerHTML = "";
        noMatchesMessage.textContent = "Could not load match history due to an error.";
        noMatchesMessage.classList.remove('hidden');
    }
}