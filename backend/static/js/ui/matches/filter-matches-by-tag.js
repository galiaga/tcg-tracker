import { authFetch } from '../../auth/auth.js';
import { updateMatchHistoryView } from "./match-list-manager.js";

async function fetchUserTags() {
    try {
        const response = await authFetch("/api/tags");
        if (!response.ok) {
             console.error("filter-matches-by-tag.js: API response not OK", response);
             throw new Error(`Failed to fetch tags: ${response.status}`);
        }
        const tags = await response.json();
        tags.sort((a, b) => a.name.localeCompare(b.name));
        return tags;
    } catch (error) {
         console.error("Error in fetchUserTags for matches:", error);
         return null;
    }
}

async function populateTagFilter() {
    const matchTagFilterSelect = document.getElementById("filter-match-tags-select");
    if (!matchTagFilterSelect) {
        console.warn("Attempted to populate tags, but select element 'filter-match-tags-select' not found.");
        return;
    }

    matchTagFilterSelect.innerHTML = '<option value="" disabled>Loading tags...</option>';

    try {
        const tags = await fetchUserTags();
        matchTagFilterSelect.innerHTML = '';

        if (!tags || tags.length === 0) {
            const option = document.createElement("option");
            option.value = "";
            option.textContent = "No tags available";
            option.disabled = true;
            matchTagFilterSelect.appendChild(option);
            return;
        }

        tags.forEach(tag => {
            const option = document.createElement("option");
            option.value = tag.id;
            option.textContent = tag.name;
            matchTagFilterSelect.appendChild(option);
        });

    } catch (error) {
        console.error("Could not populate match tag filter:", error);
        matchTagFilterSelect.innerHTML = '<option value="" disabled>Error loading tags</option>';
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const matchTagFilterSelect = document.getElementById("filter-match-tags-select");

    if (!matchTagFilterSelect) {
        return;
    }

    populateTagFilter(); 

    matchTagFilterSelect.addEventListener("change", updateMatchHistoryView);

});

export { populateTagFilter };