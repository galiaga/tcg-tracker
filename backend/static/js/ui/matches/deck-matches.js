import { formatMatchResult } from "../../utils.js"; // Ensure this path is correct
import { authFetch } from '../../auth/auth.js';

// This module now exports a function to be called explicitly.

/**
 * Fetches and renders recent matches for a specific deck into a target container.
 * @param {number} deckId - The ID of the deck to fetch matches for.
 * @param {string} targetContainerId - The ID of the HTML element to render matches into.
 * @param {number} [limit=5] - The maximum number of matches to fetch.
 */
export async function loadDeckMatchesIntoContainer(deckId, targetContainerId, limit = 5) {
    const targetContainer = document.getElementById(targetContainerId);

    if (!targetContainer) {
        console.error(`[deck-matches.js] Target container #${targetContainerId} not found.`);
        // Optionally, you could throw an error here or handle it in the calling function
        return; 
    }
    if (!deckId) {
        console.error("[deck-matches.js] Deck ID is required to load matches.");
        targetContainer.innerHTML = '<p class="text-sm text-red-500 dark:text-red-400 italic">Error: Deck ID missing.</p>';
        return;
    }

    targetContainer.innerHTML = '<p class="text-sm text-gray-500 dark:text-gray-400 italic">Loading recent matches...</p>';

    try {
        const apiUrl = `/api/matches_history?deck_id=${deckId}&limit=${limit}&offset=0`;
        const response = await authFetch(apiUrl);

        if (!response) {
            // authFetch likely handled error/redirect or threw its own error
            console.error("[deck-matches.js] authFetch call did not return a response.");
            targetContainer.innerHTML = '<p class="text-sm text-red-500 dark:text-red-400 italic">Could not load matches (network/auth issue).</p>';
            return;
        }

        if (!response.ok) {
            let errorMsg = `Error loading matches (${response.status})`;
            try {
                const errorData = await response.json();
                errorMsg = errorData.error || errorData.message || errorMsg; // Prefer backend's error message
            } catch (e) { /* Ignore if parsing JSON fails, use status-based message */ }
            
            console.error(`[deck-matches.js] API Error: ${errorMsg}`);
            targetContainer.innerHTML = `<p class="text-sm text-red-500 dark:text-red-400 italic">${errorMsg}</p>`;
            if (typeof showFlashMessage === 'function') showFlashMessage(errorMsg, "danger");
            return;
        }

        let deckMatches = await response.json();

        if (!Array.isArray(deckMatches)) {
            console.warn("[deck-matches.js] Unexpected response format, expected array:", deckMatches);
            deckMatches = []; // Treat as empty if format is wrong
        }

        targetContainer.innerHTML = ''; // Clear "Loading..." or previous content

        if (deckMatches.length === 0) {
            // Check if a dedicated "no matches" message element exists for this container
            const noMatchesMessageElement = document.getElementById(`no-matches-message-${targetContainerId}`); // Convention
            if (noMatchesMessageElement) {
                noMatchesMessageElement.textContent = "No recent matches recorded for this deck.";
                noMatchesMessageElement.classList.remove('hidden');
            } else {
                targetContainer.innerHTML = '<p class="text-sm text-gray-500 dark:text-gray-400 italic">No recent matches recorded for this deck.</p>';
            }
            return;
        }

        const list = document.createElement('ul');
        list.className = 'space-y-2'; // Adjusted spacing

        deckMatches.forEach(match => {
            const listItem = document.createElement('li');
            // Added padding and slightly more distinct separation
            listItem.className = 'flex justify-between items-center text-sm py-2.5 border-b border-gray-100 dark:border-gray-700/60 last:border-b-0';

            const resultText = formatMatchResult(match.result); // Uses your existing utility
            let resultColorClass = 'text-gray-700 dark:text-gray-200';
            const lowerResult = resultText.toLowerCase();

            if (lowerResult === 'win') resultColorClass = 'text-green-600 dark:text-green-400 font-semibold';
            else if (lowerResult === 'loss') resultColorClass = 'text-red-600 dark:text-red-400 font-semibold';
            else if (lowerResult === 'draw') resultColorClass = 'text-yellow-500 dark:text-yellow-400 font-medium';
            
            const positionText = match.player_position 
                ? `<span class="text-xs text-gray-400 dark:text-gray-500 ml-1.5">(P${match.player_position})</span>` 
                : '';

            const dateText = match.date 
                ? new Date(match.date).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
                : 'N/A';

            listItem.innerHTML = `
                <div>
                    <span class="${resultColorClass}">${resultText}</span>
                    ${positionText}
                </div>
                <span class="text-xs text-gray-500 dark:text-gray-400">${dateText}</span>
            `;
            // Future: listItem.addEventListener('click', () => showFullMatchDetailsModal(match.id));
            list.appendChild(listItem);
        });
        
        targetContainer.appendChild(list);

    } catch (error) {
        console.error(`[deck-matches.js] Error fetching or rendering matches for deck ${deckId}:`, error);
        targetContainer.innerHTML = `<p class="text-sm text-red-500 dark:text-red-400 italic">Could not load matches: ${error.message || 'Unknown error'}</p>`;
        if (typeof showFlashMessage === 'function') {
            showFlashMessage(error.message || "An unexpected error occurred while loading matches.", "danger");
        }
    }
}