import { formatMatchResult } from "../../utils.js";

document.addEventListener("DOMContentLoaded", () => loadDeckMatches());

async function loadDeckMatches() {
    const matchesTableBody = document.querySelector("#matches-list tbody");
    const noMatchesMessage = document.getElementById("no-matches-message");

    if (!matchesTableBody || !noMatchesMessage) {
        console.error("Required UI elements (#matches-list tbody or #no-matches-message) not found.");
        return;
    }

    matchesTableBody.innerHTML = "";
    noMatchesMessage.classList.add('hidden');

    const pathParts = window.location.pathname.split("/");
    const idSlug = pathParts[pathParts.length - 1];
    let deckId;

    try {
         deckId = parseInt(idSlug.split("-")[0], 10);
         if (isNaN(deckId)) {
             throw new Error("Invalid Deck ID format in URL");
         }
    } catch (error) {
        console.error("Error parsing Deck ID:", error);
        showFlashMessage("Invalid Deck ID in URL.", "danger");
        return;
    }

    try {
        const token = localStorage.getItem("access_token");
        if (!token) {
            showFlashMessage("Authentication required.", "warning");
            return;
        }

        const response = await authFetch(`/api/matches_history?deck_id=${deckId}&limit=5&offset=0`, {
            method: "GET",
            headers: {
                "Authorization": `Bearer ${token}`
            }
        });

        if (!response.ok) {
             let errorMsg = `Error loading matches (${response.status})`;
             try {
                 const errorData = await response.json();
                 errorMsg = errorData.message || errorMsg;
             } catch(e) { /* Ignore non-JSON error body */ }

             if (response.status === 404) {
                 showFlashMessage("Matches not found for this deck.", "warning");
             } else {
                showFlashMessage(errorMsg, "danger");
             }
             return;
         }

        let deckMatches = await response.json();

        if (!Array.isArray(deckMatches)) {
            console.warn("Unexpected response format, expected array:", deckMatches);
            deckMatches = [];
        }

        if (deckMatches.length === 0) {
            noMatchesMessage.classList.remove('hidden');
            matchesTableBody.innerHTML = "";
            return;
        }

        const fragment = document.createDocumentFragment();

        deckMatches.forEach(match => {
            const row = document.createElement("tr");
            row.classList.add('hover:bg-gray-50');

            const formattedDate = new Date(match.date).toLocaleString(undefined, {
                year: 'numeric', month: '2-digit', day: '2-digit',
                hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false
            });

            const resultText = formatMatchResult(match.result);
            let resultColorClass = 'text-gray-900';
            const lowerResult = resultText.toLowerCase();

            if (lowerResult === 'win') {
                resultColorClass = 'text-green-600 font-semibold';
            } else if (lowerResult === 'loss') {
                resultColorClass = 'text-red-600 font-semibold';
            } else if (lowerResult === 'draw') {
                resultColorClass = 'text-yellow-600';
            }

            row.innerHTML = `
                <td class="px-4 py-2 whitespace-nowrap text-sm font-medium ${resultColorClass}">
                    ${resultText}
                </td>
                <td class="px-4 py-2 whitespace-nowrap text-sm text-gray-500">
                    ${formattedDate}
                </td>
            `;

            fragment.appendChild(row);
        });

        matchesTableBody.appendChild(fragment);

    } catch (error) {
        console.error("Error fetching or rendering matches:", error);
        showFlashMessage(error.message || "An unexpected error occurred while loading matches.", "danger");
        matchesTableBody.innerHTML = "";
        noMatchesMessage.textContent = "Could not load matches.";
        noMatchesMessage.classList.remove('hidden');
    }
};