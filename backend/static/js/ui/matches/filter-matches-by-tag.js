import { authFetch } from '../../auth/auth.js';
import { updateMatchHistoryView } from "./match-list-manager.js";
import { fetchUserTags } from '../tagUtils.js';

async function fetchUserTagsInternal() { 
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

export async function populateTagFilter() { 
    const optionsContainer = document.getElementById("match-tag-filter-options");
    const filterButton = document.getElementById("match-tag-filter-button");

    if (!optionsContainer || !filterButton) {
        console.warn("Attempted to populate tags, but filter button or options container not found.");
        return;
    }

    optionsContainer.innerHTML = '<div class="text-center text-xs text-gray-500 py-2">Loading tags...</div>';
    const clearButton = document.getElementById("clear-match-tag-filter-button");

    try {
        const tags = await fetchUserTags();
        optionsContainer.innerHTML = '';

        if (!tags || tags.length === 0) {
            optionsContainer.innerHTML = '<div class="px-3 py-2 text-sm text-gray-500">No tags available</div>';
            if (clearButton) clearButton.classList.add('hidden');
            return;
        }

        if (clearButton) clearButton.classList.remove('hidden');
        tags.forEach(tag => {
            const div = document.createElement('div');
            div.className = 'flex items-center px-2 py-1.5';
            const checkboxId = `match-tag-filter-${tag.id}`;
            div.innerHTML = `
                <input id="${checkboxId}" name="match_tag_filter" type="checkbox" value="${tag.id}" class="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500 cursor-pointer">
                <label for="${checkboxId}" class="ml-2 block text-sm text-gray-700 hover:text-gray-900 cursor-pointer flex-grow">${tag.name}</label>
            `;
            const checkbox = div.querySelector('input');
            checkbox.addEventListener('change', () => {
                updateButtonText();
                updateMatchHistoryView();
            });
             const label = div.querySelector('label');
             label.addEventListener('click', (e) => {
                 if (e.target === label) checkbox.click();
             });
            optionsContainer.appendChild(div);
        });
        updateButtonText();

    } catch (error) {
        console.error("Could not populate match tag filter:", error);
        optionsContainer.innerHTML = '<div class="px-3 py-2 text-sm text-red-500">Error loading tags</div>';
        if (clearButton) clearButton.classList.add('hidden');
    }
}

function updateButtonText() {
    const optionsContainer = document.getElementById("match-tag-filter-options");
    const buttonTextElement = document.getElementById('match-tag-filter-button-text');
    const clearButton = document.getElementById("clear-match-tag-filter-button");
    if (!optionsContainer || !buttonTextElement || !clearButton) return;
    const checkedBoxes = optionsContainer.querySelectorAll('input[type="checkbox"]:checked');
    if (checkedBoxes.length === 0) {
        buttonTextElement.textContent = "All Tags";
        clearButton.classList.add('text-gray-400', 'pointer-events-none');
        clearButton.classList.remove('text-blue-600', 'hover:text-blue-800');
    } else {
         clearButton.classList.remove('text-gray-400', 'pointer-events-none');
         clearButton.classList.add('text-blue-600', 'hover:text-blue-800');
         if (checkedBoxes.length === 1) {
             const label = optionsContainer.querySelector(`label[for="${checkedBoxes[0].id}"]`);
             buttonTextElement.textContent = label ? label.textContent : "1 tag selected";
         } else {
             buttonTextElement.textContent = `${checkedBoxes.length} tags selected`;
         }
    }
}

function toggleDropdown(show) {
    const filterButton = document.getElementById("match-tag-filter-button");
    const tagFilterDropdown = document.getElementById("match-tag-filter-dropdown");
    if (!filterButton || !tagFilterDropdown) return;
    const isOpen = typeof show === 'boolean' ? show : tagFilterDropdown.classList.contains('hidden');
    tagFilterDropdown.classList.toggle('hidden', !isOpen);
    filterButton.setAttribute('aria-expanded', isOpen);
}

function clearTagSelection() {
    const optionsContainer = document.getElementById("match-tag-filter-options");
    if (!optionsContainer) return;
    const checkedBoxes = optionsContainer.querySelectorAll('input[type="checkbox"]:checked');
    if (checkedBoxes.length > 0) {
         checkedBoxes.forEach(checkbox => {
             checkbox.checked = false;
         });
         updateButtonText();
         updateMatchHistoryView();
    }
    toggleDropdown(false);
}

document.addEventListener("DOMContentLoaded", () => {
    const tagFilterButton = document.getElementById("match-tag-filter-button");
    const tagFilterDropdown = document.getElementById("match-tag-filter-dropdown");
    const tagFilterOptionsContainer = document.getElementById("match-tag-filter-options");
    const clearButton = document.getElementById("clear-match-tag-filter-button");

    if (!tagFilterButton || !tagFilterDropdown || !tagFilterOptionsContainer || !clearButton) {
        return;
    }

    populateTagFilter();
    tagFilterButton.addEventListener('click', (e) => {
        e.stopPropagation();
        toggleDropdown();
    });
    clearButton.addEventListener('click', clearTagSelection);
    document.addEventListener('click', (event) => {
        if (!tagFilterButton.contains(event.target) && !tagFilterDropdown.contains(event.target) && !tagFilterDropdown.classList.contains('hidden')) {
            toggleDropdown(false);
        }
    });
});
