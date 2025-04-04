import { authFetch } from '../../auth/auth.js';
import { updateMatchHistoryView } from "./match-list-manager.js";
import { fetchUserTags } from '../tagUtils.js';

async function populateTagFilter() {
    const matchTagFilterSelect = document.getElementById("filter-match-tags-select");
    const optionsContainer = document.getElementById("match-tag-filter-options");
    const filterButton = document.getElementById("match-tag-filter-button");

    if (!optionsContainer || !filterButton) { 
        console.warn("Attempted to populate tags, but filter button or options container not found.");
        return; 
    }


    optionsContainer.innerHTML = '<div class="text-center text-xs text-gray-500 py-2">Loading tags...</div>';

    try {
        const tags = await fetchUserTags();
        optionsContainer.innerHTML = '';

        if (!tags || tags.length === 0) {
            optionsContainer.innerHTML = '<div class="px-3 py-2 text-sm text-gray-500">No tags available</div>';
            return;
        }

        tags.forEach(tag => {
            const div = document.createElement('div');
            div.className = 'flex items-center px-2 py-1';
            const checkboxId = `match-tag-filter-${tag.id}`;
            div.innerHTML = `
                <input id="${checkboxId}" name="match_tag_filter" type="checkbox" value="${tag.id}" class="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500">
                <label for="${checkboxId}" class="ml-2 block text-sm text-gray-900 cursor-pointer">${tag.name}</label>
            `;
            const checkbox = div.querySelector('input');
            checkbox.addEventListener('change', () => {
                updateButtonText();
                updateMatchHistoryView();
            });
            optionsContainer.appendChild(div);
        });
        updateButtonText();

    } catch (error) {
        console.error("Could not populate match tag filter:", error);
        optionsContainer.innerHTML = '<div class="px-3 py-2 text-sm text-red-500">Error loading tags</div>';
    }
}

function updateButtonText() {
    const optionsContainer = document.getElementById("match-tag-filter-options");
    const buttonTextElement = document.getElementById('match-tag-filter-button-text');
    if (!optionsContainer || !buttonTextElement) return;

    const checkedBoxes = optionsContainer.querySelectorAll('input[type="checkbox"]:checked');

    if (checkedBoxes.length === 0) {
        buttonTextElement.textContent = "All Tags";
    } else if (checkedBoxes.length === 1) {
        const label = optionsContainer.querySelector(`label[for="${checkedBoxes[0].id}"]`);
        buttonTextElement.textContent = label ? label.textContent : "1 tag selected";
    } else {
        buttonTextElement.textContent = `${checkedBoxes.length} tags selected`;
    }
}

function toggleDropdown() {
    const filterButton = document.getElementById("match-tag-filter-button");
    const tagFilterDropdown = document.getElementById("match-tag-filter-dropdown");
    if (!filterButton || !tagFilterDropdown) return;

    const isOpen = !tagFilterDropdown.classList.contains('hidden');
    tagFilterDropdown.classList.toggle('hidden', isOpen);
    filterButton.setAttribute('aria-expanded', !isOpen);
}

document.addEventListener("DOMContentLoaded", () => {
    const optionsContainer = document.getElementById("match-tag-filter-options");
    const filterButton = document.getElementById("match-tag-filter-button");
    const tagFilterDropdown = document.getElementById("match-tag-filter-dropdown");


    if (!filterButton || !tagFilterDropdown || !optionsContainer) {
        return;
    }

    populateTagFilter();

    filterButton.addEventListener('click', toggleDropdown);

    document.addEventListener('click', (event) => {
        if (!filterButton.contains(event.target) && !tagFilterDropdown.contains(event.target) && !tagFilterDropdown.classList.contains('hidden')) {
             toggleDropdown();
        }
    });

});

export { populateTagFilter };