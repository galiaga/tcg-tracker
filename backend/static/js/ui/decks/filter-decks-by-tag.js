import { authFetch } from '../../auth/auth.js';
import { updateDeckListView } from "./deck-list-manager.js";
import { fetchUserTags } from '../tagUtils.js';

document.addEventListener("DOMContentLoaded", () => {
    const tagFilterButton = document.getElementById("tag-filter-button");
    const tagFilterDropdown = document.getElementById("tag-filter-dropdown");
    const tagFilterOptionsContainer = document.getElementById("tag-filter-options");
    const clearButton = document.getElementById("clear-tag-filter-button"); 

    if (!tagFilterButton || !tagFilterDropdown || !tagFilterOptionsContainer || !clearButton) { 
        console.warn("Deck tag filter UI elements (button, dropdown, options, clear button) not found.");
        return;
    }

    let isDropdownOpen = false;

    async function populateTagFilter() {
        try {
            const tags = await fetchUserTags();
            tagFilterOptionsContainer.innerHTML = '';

            if (!tags || tags.length === 0) {
                tagFilterOptionsContainer.innerHTML = '<div class="px-3 py-2 text-sm text-gray-500">No tags available</div>';
                clearButton.classList.add('hidden');
                return;
            }

            clearButton.classList.remove('hidden');
            tags.forEach(tag => {
                const div = document.createElement('div');
                div.className = 'flex items-center px-2 py-1.5'; 
                const checkboxId = `deck-tag-filter-${tag.id}`;
                div.innerHTML = `
                    <input id="${checkboxId}" name="deck_tag_filter" type="checkbox" value="${tag.id}" class="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500 cursor-pointer">
                    <label for="${checkboxId}" class="ml-2 block text-sm text-gray-700 hover:text-gray-900 cursor-pointer flex-grow">${tag.name}</label>
                `;
                const checkbox = div.querySelector('input');
                checkbox.addEventListener('change', () => {
                    updateButtonText();
                    updateDeckListView();
                });
                 const label = div.querySelector('label');
                 label.addEventListener('click', (e) => {
                     if (e.target === label) checkbox.click();
                 });

                tagFilterOptionsContainer.appendChild(div);
            });
            updateButtonText();

        } catch (error) {
            console.error("Could not populate deck tag filter:", error);
            tagFilterOptionsContainer.innerHTML = '<div class="px-3 py-2 text-sm text-red-500">Error loading tags</div>';
             clearButton.classList.add('hidden');
        }
    }

    function updateButtonText() {
        const checkedBoxes = tagFilterOptionsContainer.querySelectorAll('input[type="checkbox"]:checked');
        const buttonTextElement = document.getElementById('tag-filter-button-text');
        if (!buttonTextElement) return;

        if (checkedBoxes.length === 0) {
            buttonTextElement.textContent = "All Tags";
            clearButton.classList.add('text-gray-400', 'pointer-events-none'); 
             clearButton.classList.remove('text-blue-600', 'hover:text-blue-800');
        } else {
             clearButton.classList.remove('text-gray-400', 'pointer-events-none'); 
             clearButton.classList.add('text-blue-600', 'hover:text-blue-800');
             if (checkedBoxes.length === 1) {
                 const label = tagFilterOptionsContainer.querySelector(`label[for="${checkedBoxes[0].id}"]`);
                 buttonTextElement.textContent = label ? label.textContent : "1 tag selected";
             } else {
                 buttonTextElement.textContent = `${checkedBoxes.length} tags selected`;
             }
        }
    }

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


    tagFilterButton.addEventListener('click', (e) => {
        e.stopPropagation();
        toggleDropdown();
    });

    clearButton.addEventListener('click', clearTagSelection);

    document.addEventListener('click', (event) => {
        if (!tagFilterButton.contains(event.target) && !tagFilterDropdown.contains(event.target) && isDropdownOpen) {
            toggleDropdown(false);
        }
    });

    populateTagFilter();

});