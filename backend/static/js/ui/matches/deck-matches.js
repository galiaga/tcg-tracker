// backend/static/js/ui/matches/deck-matches.js
import { formatMatchResult } from "../../utils.js"; // Ensure this path is correct
import { authFetch } from '../../auth/auth.js';

// Removed: document.addEventListener("DOMContentLoaded", () => loadDeckMatches());
// This module will now be called explicitly by other scripts (like deck-details.js)

export async function loadDeckMatches(deckId, targetContainerId, limit = 5) {
    const targetContainer = document.getElementById(targetContainerId);

    if (!targetContainer) {
        console.error(`[deck-matches.js] Target container #${targetContainerId} not found.`);
        return;
    }
    if (!deckId) {
        console.error("[deck-matches.js] Deck ID is required to load matches.");
        targetContainer.innerHTML = '<p class="text-sm text-red-500 dark:text-red-400">Error: Deck ID missing.</p>';
        return;
    }

    targetContainer.innerHTML = '<p class="text-sm text-gray-500 dark:text-gray-400">Loading recent matches...</p>';

    try {
        const apiUrl = `/api/matches_history?deck_id=${deckId}&limit=${limit}&offset=0`;
        const response = await authFetch(apiUrl);

        if (!response) {
            console.error("[deck-matches.js] authFetch failed, likely handled error.");
            targetContainer.innerHTML = '<p class="text-sm text-red-500 dark:text-red-400">Could not load matches (auth/network error).</p>';
            return;
        }
        // 401 should be handled by authFetch redirecting to login

        if (!response.ok) {
            let errorMsg = `Error loading matches (${response.status})`;
            try {
                const errorData = await response.json();
                errorMsg = errorData.error || errorMsg; // Use 'error' key from backend
            } catch (e) { /* Ignore if parsing JSON fails */ }

            targetContainer.innerHTML = `<p class="text-sm text-red-500 dark:text-red-400">${errorMsg}</p>`;
            if (typeof showFlashMessage === 'function') showFlashMessage(errorMsg, "danger");
            return;
        }

        let deckMatches = await response.json();

        if (!Array.isArray(deckMatches)) {
            console.warn("[deck-matches.js] Unexpected response format, expected array:", deckMatches);
            deckMatches = [];
        }

        if (deckMatches.length === 0) {
            targetContainer.innerHTML = '<p class="text-sm text-gray-500 dark:text-gray-400">No recent matches recorded for this deck.</p>';
            return;
        }

        // Render as a list instead of a table for embedding
        const list = document.createElement('ul');
        list.className = 'space-y-3 mt-2'; // Add some spacing

        deckMatches.forEach(match => {
            const listItem = document.createElement('li');
            listItem.className = 'flex justify-between items-center text-sm pb-2 border-b border-gray-200 dark:border-gray-700 last:border-b-0';

            const resultText = formatMatchResult(match.result);
            let resultColorClass = 'text-gray-700 dark:text-gray-300';
            const lowerResult = resultText.toLowerCase();

            if (lowerResult === 'win') resultColorClass = 'text-green-600 dark:text-green-400 font-semibold';
            else if (lowerResult === 'loss') resultColorClass = 'text-red-600 dark:text-red-400 font-semibold';
            else if (lowerResult === 'draw') resultColorClass = 'text-yellow-600 dark:text-yellow-400';
            
            const positionText = match.player_position 
                ? `<span class="text-xs text-gray-500 dark:text-gray-400 ml-2">(Pos: ${match.player_position})</span>` 
                : '';

            const dateText = match.date 
                ? new Date(match.date).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })
                : 'N/A';

            listItem.innerHTML = `
                <div>
                    <span class="${resultColorClass}">${resultText}</span>
                    ${positionText}
                </div>
                <span class="text-gray-500 dark:text-gray-400">${dateText}</span>
            `;
            list.appendChild(listItem);
        });

        targetContainer.innerHTML = ''; // Clear "Loading..."
        targetContainer.appendChild(list);

    } catch (error) {
        console.error("[deck-matches.js] Error fetching or rendering matches:", error);
        targetContainer.innerHTML = `<p class="text-sm text-red-500 dark:text-red-400">Could not load matches: ${error.message || 'Unknown error'}</p>`;
        if (typeof showFlashMessage === 'function') showFlashMessage(error.message || "An unexpected error occurred while loading matches.", "danger");
    }
}