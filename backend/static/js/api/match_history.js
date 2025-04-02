import { formatMatchResult } from "../utils.js";

document.addEventListener("DOMContentLoaded", () => loadUserMatches());

async function loadUserMatches() {
    const matchesListContainer = document.getElementById("matches-list-items");
    const noMatchesMessage = document.getElementById("no-matches-message-history");

    if (!matchesListContainer || !noMatchesMessage) {
        console.error("Required UI elements for match history list not found.");
        return;
    }

    matchesListContainer.innerHTML = `<div class="p-6 text-center text-gray-400">Loading match history...</div>`;
    noMatchesMessage.classList.add('hidden');

    try {
        const token = localStorage.getItem("access_token");
        if (!token) {
            showFlashMessage("Authentication required to view match history.", "warning");
            matchesListContainer.innerHTML = "";
            noMatchesMessage.textContent = "Please log in to view history.";
            noMatchesMessage.classList.remove('hidden');
            return;
        }

        const response = await authFetch("/api/matches_history", {
            method: "GET",
            headers: { "Authorization": `Bearer ${token}` }
        });

        if (!response.ok) {
             let errorMsg = `Error loading match history (${response.status})`;
             try { const errorData = await response.json(); errorMsg = errorData.message || errorMsg; } catch(e) {}
             showFlashMessage(errorMsg, "danger");
             matchesListContainer.innerHTML = "";
             noMatchesMessage.textContent = "Could not load match history.";
             noMatchesMessage.classList.remove('hidden');
             return;
         }

        let userMatches = await response.json();

        if (!Array.isArray(userMatches)) {
            console.warn("Unexpected response format for match history:", userMatches);
            userMatches = [];
        }

        matchesListContainer.innerHTML = "";

        if (userMatches.length === 0) {
            noMatchesMessage.textContent = "No match history found.";
            noMatchesMessage.classList.remove('hidden');
            return;
        }

        const fragment = document.createDocumentFragment();

        userMatches.forEach(match => {
            const itemContainer = document.createElement("div");

            const resultText = formatMatchResult(match.result);
            const lowerResult = resultText.toLowerCase();

            let cardBgColorClass = 'bg-white';
            let badgeBgColorClass = 'bg-gray-200';
            let badgeTextColorClass = 'text-gray-800';

            if (lowerResult === 'win') {
                cardBgColorClass = 'bg-green-50';
                badgeBgColorClass = 'bg-green-600';
                badgeTextColorClass = 'text-white';
            } else if (lowerResult === 'loss') {
                cardBgColorClass = 'bg-red-50';
                badgeBgColorClass = 'bg-red-600';
                badgeTextColorClass = 'text-white';
            } else if (lowerResult === 'draw') {
                cardBgColorClass = 'bg-yellow-50';
                badgeBgColorClass = 'bg-yellow-500';
                badgeTextColorClass = 'text-white';
            }

            itemContainer.className = `p-2 border border-gray-200 rounded-lg shadow-sm md:shadow-none md:border-0 md:border-b md:rounded-none md:p-0 md:flex md:items-center ${cardBgColorClass} md:bg-transparent md:hover:bg-gray-50`;

            const formattedDate = match.date
                ? new Date(match.date).toLocaleString(undefined, { dateStyle: 'short', timeStyle: 'short' })
                : 'N/A';

            itemContainer.innerHTML = `
                <div class="grid grid-cols-2 gap-x-2 gap-y-1 text-sm md:flex md:w-full md:items-center">

                    <div class="col-span-2 md:flex-1 md:px-4 md:py-2 md:whitespace-nowrap">
                        <span class="text-xs font-medium text-gray-500 md:hidden">Deck: </span>
                        <span class="text-gray-800 font-medium">${match.deck.name || 'N/A'}</span>
                    </div>

                    <div class="text-left md:flex-1 md:px-4 md:py-2 md:whitespace-nowrap">
                        <span class="text-xs font-medium text-gray-500 md:hidden">Type: </span>
                        <span class="text-gray-700">${match.deck_type.name || 'N/A'}</span>
                    </div>

                    <div class="text-right md:text-left md:w-24 md:px-4 md:py-2 md:whitespace-nowrap">
                        <span class="text-xs font-medium text-gray-500 mr-1 md:hidden">Result:</span>
                        <span class="inline-block px-2.5 py-0.5 rounded-md text-xs font-medium ${badgeBgColorClass} ${badgeTextColorClass}">
                            ${resultText}
                        </span>
                    </div>

                     <div class="col-span-2 md:flex-1 md:px-4 md:py-2 md:whitespace-nowrap">
                         <span class="text-xs font-medium text-gray-500 md:hidden">Date: </span>
                         <span class="text-gray-700">${formattedDate}</span>
                    </div>
                </div>
            `;
            fragment.appendChild(itemContainer);
        });

        matchesListContainer.appendChild(fragment);

    } catch (error) {
        console.error("Error fetching or rendering match history:", error);
        showFlashMessage(error.message || "An unexpected error occurred loading history.", "danger");
        matchesListContainer.innerHTML = "";
        noMatchesMessage.textContent = "Could not load match history due to an error.";
        noMatchesMessage.classList.remove('hidden');
    }
}