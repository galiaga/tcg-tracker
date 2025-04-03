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

    try {
        const token = localStorage.getItem("access_token");
        if (!token) {
            showFlashMessage("Authentication required to view match history.", "warning");
            loadingMessage.textContent = "Please log in to view history.";
            noMatchesMessage.textContent = "Please log in to view history.";
            noMatchesMessage.classList.remove('hidden');
            matchesListContainer.innerHTML = '';
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

        const fragment = document.createDocumentFragment();
        const locale = navigator.language || 'en-US';
        const dateOptions = { dateStyle: 'short', timeStyle: 'short' };

        userMatches.forEach(match => {
            const itemContainer = document.createElement("div");
            const resultText = formatMatchResult(match.result);
            const lowerResult = resultText.toLowerCase();

            let badgeBgColorClass = 'bg-gray-400';
            let badgeTextColorClass = 'text-white';

            if (lowerResult === 'win') {
                badgeBgColorClass = 'bg-green-600';
            } else if (lowerResult === 'loss') {
                badgeBgColorClass = 'bg-red-600';
            } else if (lowerResult === 'draw') {
                badgeBgColorClass = 'bg-yellow-500';
            }

            itemContainer.className = `p-3 border-b border-gray-200 md:border-0 md:p-0 md:flex md:items-center hover:bg-gray-50`;

            let formattedDate = 'N/A';
             if (match.date) {
                 try {
                     formattedDate = new Date(match.date).toLocaleString(locale, dateOptions);
                 } catch(e) {
                     console.warn(`Could not format date: ${match.date}`, e);
                     formattedDate = match.date;
                 }
             }

            itemContainer.innerHTML = `
                <div class="grid grid-cols-2 gap-x-2 gap-y-1 text-sm md:flex md:w-full md:items-center">
                    <div class="col-span-2 md:flex-1 md:px-4 md:py-3 md:whitespace-nowrap">
                        <span class="text-xs font-medium text-gray-500 md:hidden">Deck: </span>
                        <span class="text-gray-800 font-medium">${match.deck?.name ?? 'N/A'}</span>
                    </div>
                    <div class="text-left md:flex-1 md:px-4 md:py-3 md:whitespace-nowrap">
                        <span class="text-xs font-medium text-gray-500 md:hidden">Type: </span>
                        <span class="text-gray-700">${match.deck_type?.name ?? 'N/A'}</span>
                    </div>
                    <div class="text-right md:text-left md:w-28 md:px-4 md:py-3 md:whitespace-nowrap">
                        <span class="text-xs font-medium text-gray-500 mr-1 md:hidden">Result:</span>
                        <span class="inline-block px-2.5 py-0.5 rounded-full text-xs font-semibold ${badgeBgColorClass} ${badgeTextColorClass}">
                            ${resultText}
                        </span>
                    </div>
                    <div class="col-span-2 md:flex-1 md:px-4 md:py-3 md:whitespace-nowrap">
                        <span class="text-xs font-medium text-gray-500 md:hidden">Date: </span>
                        <span class="text-gray-700">${formattedDate}</span>
                    </div>
                </div>
            `;
            fragment.appendChild(itemContainer);
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