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

    if (checkedBoxes.length === 0) {
        buttonTextElement.textContent = "All Tags";
        clearButton.classList.add('text-gray-400', 'pointer-events-none');
        clearButton.classList.remove('text-violet-600', 'hover:text-violet-800');
    } else {
        clearButton.classList.remove('text-gray-400', 'pointer-events-none');
        clearButton.classList.add('text-violet-600', 'hover:text-violet-800');
        if (checkedBoxes.length === 1) {
            const label = tagFilterOptionsContainer.querySelector(`label[for="${checkedBoxes[0].id}"]`);
            buttonTextElement.textContent = label ? label.textContent : "1 tag selected";
        } else {
            buttonTextElement.textContent = `${checkedBoxes.length} tags selected`;
        }
    }
}

export async function populateTagFilter() {
    console.log("[filter-decks-by-tag] Attempting to populate tag filter...");
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

    tagFilterOptionsContainer.innerHTML = '<div class="px-3 py-2 text-sm text-violet-500">Loading tags...</div>';
    clearButton.classList.add('hidden'); 

    try {
        const tags = await fetchUserTags(); 
        console.log("[filter-decks-by-tag] Fetched tags for filter:", tags);
        tagFilterOptionsContainer.innerHTML = '';

        if (!tags || tags.length === 0) {
            tagFilterOptionsContainer.innerHTML = '<div class="px-3 py-2 text-sm text-gray-500">No tags available</div>';
            return;
        }

        clearButton.classList.remove('hidden');

        tags.sort((a, b) => a.name.localeCompare(b.name));

        const fragment = document.createDocumentFragment();
        tags.forEach(tag => {
            const div = document.createElement('div');
            div.className = 'flex items-center px-2 py-1.5';
            const checkboxId = `deck-tag-filter-${tag.id}`;
            const isChecked = previouslySelectedIds.has(String(tag.id));

            div.innerHTML = `
                <input id="${checkboxId}" name="deck_tag_filter" type="checkbox" value="${tag.id}" ${isChecked ? 'checked' : ''}
                       class="h-4 w-4 rounded border-gray-300 text-violet-600 focus:ring-violet-500 cursor-pointer tag-filter-checkbox">
                <label for="${checkboxId}" class="ml-2 block text-sm text-gray-700 hover:text-gray-900 cursor-pointer flex-grow">${tag.name}</label>
            `;
            fragment.appendChild(div);
        });
        tagFilterOptionsContainer.appendChild(fragment);

        updateButtonText();
        console.log("[filter-decks-by-tag] Finished populating tag filter.");

    } catch (error) {
        console.error("Could not populate deck tag filter:", error);
        tagFilterOptionsContainer.innerHTML = '<div class="px-3 py-2 text-sm text-red-500">Error loading tags</div>';
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

    tagFilterOptionsContainer.addEventListener('change', (event) => {
        if (event.target.matches('input[name="deck_tag_filter"]')) {
            updateButtonText(); 
            updateDeckListView(); 
        }
    });

    tagFilterButton.addEventListener('click', (e) => {
        e.stopPropagation(); 
        toggleDropdown();
    });

    clearButton.addEventListener('click', clearTagSelection);

    document.addEventListener('click', (event) => {
        if (isDropdownOpen && !tagFilterButton.contains(event.target) && !tagFilterDropdown.contains(event.target)) {
            toggleDropdown(false);
        }
    });


});