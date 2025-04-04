import { authFetch } from '../../auth/auth.js';
import { updateDeckListView } from "./deck-list-manager.js";

document.addEventListener("DOMContentLoaded", () => {
    const tagFilterSelect = document.getElementById("filter-tags-select");

    if (!tagFilterSelect) {
        return;
    }

    async function populateTagFilter() {
        try {
            const tags = await fetchUserTags();

            tagFilterSelect.innerHTML = '';

            if (!tags || tags.length === 0) {
                const option = document.createElement("option");
                option.value = "";
                option.textContent = "No tags available";
                option.disabled = true;
                tagFilterSelect.appendChild(option);
                return;
            }

            tags.forEach(tag => {
                const option = document.createElement("option");
                option.value = tag.id;
                option.textContent = tag.name;
                tagFilterSelect.appendChild(option);
            });

        } catch (error) {
            tagFilterSelect.innerHTML = '<option value="" disabled>Error loading tags</option>';
        }
    }

    async function fetchUserTags() {
        try {
            const response = await authFetch("/api/tags");
            if (!response.ok) {
                 console.error("filter-decks-by-tag.js: API response not OK", response);
                 throw new Error(`Failed to fetch tags: ${response.status}`);
            }
            const tags = await response.json();
            tags.sort((a, b) => a.name.localeCompare(b.name));
            return tags;
        } catch (error) {
            return null;
        }
    }

    populateTagFilter();

    tagFilterSelect.addEventListener("change", updateDeckListView);

});