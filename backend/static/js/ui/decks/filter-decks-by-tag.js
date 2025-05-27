// backend/static/js/ui/decks/filter-decks-by-tag.js

import { authFetch } from '../../auth/auth.js';
import { updateDeckListView } from "./deck-list-manager.js";
import { fetchUserTags } from '../tag-utils.js';


function updateButtonText() {
    const tagFilterOptionsContainer = document.getElementById("tag-filter-options");
    const buttonTextElement = document.getElementById('tag-filter-button-text');
    const clearButton = document.getElementById("clear-tag-filter-button");

    if (!tagFilterOptionsContainer || !buttonTextElement || !clearButton) {
        console.warn("Cannot update tag filter button text: required elements missing.");
        return;
    }

    const checkedBoxes = tagFilterOptionsContainer.querySelectorAll('input[type="checkbox"]:checked');

    // Define classes for clearButton states
    // Active state classes are mostly from its HTML, ensure JS aligns
    const activeClasses = ['text-violet-600', 'dark:text-violet-300', 'hover:text-violet-900', 'dark:hover:text-violet-100'];
    const disabledClasses = ['text-gray-400', 'dark:text-gray-500', 'pointer-events-none'];


    if (checkedBoxes.length === 0) {
        buttonTextElement.textContent = "All Tags";
        clearButton.classList.remove(...activeClasses);
        clearButton.classList.add(...disabledClasses);
    } else {
        clearButton.classList.remove(...disabledClasses);
        clearButton.classList.add(...activeClasses);
        if (checkedBoxes.length === 1) {
            const label = tagFilterOptionsContainer.querySelector(`label[for="${checkedBoxes[0].id}"]`);
            buttonTextElement.textContent = label ? label.textContent : "1 tag selected";
        } else {
            buttonTextElement.textContent = `${checkedBoxes.length} tags selected`;
        }
    }
}

export async function populateTagFilter() {
    const tagFilterOptionsContainer = document.getElementById("tag-filter-options");
    const clearButton = document.getElementById("clear-tag-filter-button");

    if (!tagFilterOptionsContainer || !clearButton) {
        console.error("Cannot populate tag filter: options container or clear button not found.");
        return;
    }

    const previouslySelectedIds = new Set();
    tagFilterOptionsContainer.querySelectorAll('input[type="checkbox"]:checked').forEach(cb => {
        if (cb.value) previouslySelectedIds.add(cb.value);
    });

    // Add dark mode text color for status messages
    tagFilterOptionsContainer.innerHTML = '<div class="px-3 py-2 text-sm text-violet-500 dark:text-violet-400">Loading tags...</div>';
    clearButton.classList.add('hidden');

    try {
        const tags = await fetchUserTags();
        tagFilterOptionsContainer.innerHTML = ''; // Clear loading message

        if (!tags || tags.length === 0) {
            tagFilterOptionsContainer.innerHTML = '<div class="px-3 py-2 text-sm text-gray-500 dark:text-gray-400">No tags available</div>';
            return;
        }

        clearButton.classList.remove('hidden');

        tags.sort((a, b) => a.name.localeCompare(b.name));

        const fragment = document.createDocumentFragment();
        tags.forEach(tag => {
            const div = document.createElement('div');
            // Add hover effect and rounding for the item container
            div.className = 'flex items-center px-2 py-1.5 rounded hover:bg-gray-100 dark:hover:bg-gray-600';
            const checkboxId = `deck-tag-filter-${tag.id}`;
            const isChecked = previouslySelectedIds.has(String(tag.id));

            // Add dark mode classes for checkbox and label
            div.innerHTML = `
                <input id="${checkboxId}" name="deck_tag_filter" type="checkbox" value="${tag.id}" ${isChecked ? 'checked' : ''}
                       class="h-4 w-4 rounded border-gray-300 dark:border-gray-600 dark:bg-gray-700 text-violet-600 focus:ring-violet-500 dark:focus:ring-offset-gray-700 cursor-pointer tag-filter-checkbox">
                <label for="${checkboxId}" class="ml-2 block text-sm text-gray-700 dark:text-gray-200 hover:text-gray-900 dark:hover:text-white cursor-pointer flex-grow">${tag.name}</label>
            `;
            fragment.appendChild(div);
        });
        tagFilterOptionsContainer.appendChild(fragment);

        updateButtonText();

    } catch (error) {
        console.error("Could not populate deck tag filter:", error);
        tagFilterOptionsContainer.innerHTML = '<div class="px-3 py-2 text-sm text-red-500 dark:text-red-400">Error loading tags</div>';
        clearButton.classList.add('hidden');
    }
}


document.addEventListener("DOMContentLoaded", () => {
    const tagFilterButton = document.getElementById("tag-filter-button");
    const tagFilterDropdown = document.getElementById("tag-filter-dropdown");
    const tagFilterOptionsContainer = document.getElementById("tag-filter-options");
    const clearButton = document.getElementById("clear-tag-filter-button");

    if (!tagFilterButton || !tagFilterDropdown || !tagFilterOptionsContainer || !clearButton) {
        console.warn("Deck tag filter UI elements not found. Listeners not attached.");
        return;
    }

    let isDropdownOpen = false;

    function toggleDropdown(show) {
        isDropdownOpen = typeof show === 'boolean' ? show : !isDropdownOpen;
        tagFilterDropdown.classList.toggle('hidden', !isDropdownOpen);
        tagFilterButton.setAttribute('aria-expanded', isDropdownOpen);
    }

    function clearTagSelection() {
        const checkedBoxes = tagFilterOptionsContainer.querySelectorAll('input[type="checkbox"]:checked');
        if (checkedBoxes.length > 0) {
             checkedBoxes.forEach(checkbox => {
                 checkbox.checked = false;
             });
             updateButtonText();
             updateDeckListView();
        }
        toggleDropdown(false);
    }

    // Use event delegation on the container for dynamically added checkboxes
    tagFilterOptionsContainer.addEventListener('change', (event) => {
        if (event.target.matches('input[name="deck_tag_filter"].tag-filter-checkbox')) {
            updateButtonText();
            updateDeckListView();
        }
    });
    
    // Also handle clicks on labels to toggle checkboxes
    tagFilterOptionsContainer.addEventListener('click', (event) => {
        const label = event.target.closest('label');
        if (label && label.htmlFor.startsWith('deck-tag-filter-')) {
            const checkbox = document.getElementById(label.htmlFor);
            if (checkbox && !event.target.matches('input[type="checkbox"]')) { // Avoid double-triggering if checkbox itself was clicked
                // checkbox.checked = !checkbox.checked; // This might cause issues if change event is also firing
                // updateButtonText(); // Change event should handle this
                // updateDeckListView(); // Change event should handle this
            }
        }
    });


    tagFilterButton.addEventListener('click', (e) => {
        e.stopPropagation();
        toggleDropdown();
    });

    clearButton.addEventListener('click', (e) => {
        e.stopPropagation(); // Prevent click from bubbling to document listener
        clearTagSelection();
    });

    document.addEventListener('click', (event) => {
        if (isDropdownOpen && !tagFilterButton.contains(event.target) && !tagFilterDropdown.contains(event.target)) {
            toggleDropdown(false);
        }
    });

    // Initial population
    // populateTagFilter(); // Consider if this should be called here or if another script handles initial load
});