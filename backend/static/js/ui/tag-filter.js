import { fetchUserTags } from './tag-utils.js';

export async function populateTagFilter(config) {
    const {
        optionsContainerId,
        filterButtonId,
        clearButtonId,
        checkboxName,
        checkboxIdPrefix,
        onFilterChange,
        noTagsMessage = "No tags available",
        loadingMessage = "Loading tags...",
        errorMessage = "Error loading tags"
    } = config;

    if (!optionsContainerId || !filterButtonId || !clearButtonId || !checkboxName || !checkboxIdPrefix) {
        console.error("populateTagFilter configuration incomplete:", config);
        return;
    }

    const optionsContainer = document.getElementById(optionsContainerId);
    const filterButton = document.getElementById(filterButtonId);
    const clearButton = document.getElementById(clearButtonId);

    if (!optionsContainer) {
        console.error(`Container with ID "${optionsContainerId}" not found.`);
        return;
    }
    if (!filterButton) console.warn(`Filter button with ID "${filterButtonId}" not found.`);
    if (!clearButton) console.warn(`Clear button with ID "${clearButtonId}" not found.`);

    optionsContainer.innerHTML = `<div class="text-center text-xs text-gray-500 py-2">${loadingMessage}</div>`;

    try {
        const tags = await fetchUserTags();
        optionsContainer.innerHTML = '';

        if (!tags || tags.length === 0) {
            optionsContainer.innerHTML = `<div class="px-3 py-2 text-sm text-gray-500">${noTagsMessage}</div>`;
            if (clearButton) clearButton.classList.add('hidden');
            return;
        }

        if (clearButton) clearButton.classList.remove('hidden');

        tags.forEach(tag => {
            const div = document.createElement('div');
            div.className = 'flex items-center px-2 py-1.5';
            const checkboxId = `${checkboxIdPrefix}-${tag.id}`;

            div.innerHTML = `
                <input id="${checkboxId}" name="${checkboxName}" type="checkbox" value="${tag.id}" class="h-4 w-4 rounded border-gray-300 text-violet-600 focus:ring-violet-500 cursor-pointer">
                <label for="${checkboxId}" class="ml-2 block text-sm text-gray-700 hover:text-gray-900 cursor-pointer flex-grow">${tag.name}</label>
            `;
            const checkbox = div.querySelector('input');

            checkbox.addEventListener('change', () => {
                if (typeof onFilterChange === 'function') {
                    onFilterChange();
                }
            });

            optionsContainer.appendChild(div);
        });

    } catch (error) {
        console.error(`Could not populate tag filter for ${optionsContainerId}:`, error);
        optionsContainer.innerHTML = `<div class="px-3 py-2 text-sm text-red-500">${errorMessage}</div>`;
        if (clearButton) clearButton.classList.add('hidden');
    }
}

export function updateButtonText(config) {
    const { optionsContainerId, buttonTextElementId, clearButtonId, buttonDefaultText = "All Tags" } = config;
    const optionsContainer = document.getElementById(optionsContainerId);
    const buttonTextElement = document.getElementById(buttonTextElementId);
    const clearButton = document.getElementById(clearButtonId);

    if (!optionsContainer || !buttonTextElement || !clearButton) return;

    const checkedBoxes = optionsContainer.querySelectorAll('input[type="checkbox"]:checked');

    if (checkedBoxes.length === 0) {
        buttonTextElement.textContent = buttonDefaultText;
        clearButton.classList.add('text-gray-400', 'pointer-events-none');
        clearButton.classList.remove('text-violet-600', 'hover:text-violet-800');
    } else {
        clearButton.classList.remove('text-gray-400', 'pointer-events-none');
        clearButton.classList.add('text-violet-600', 'hover:text-violet-800');

        if (checkedBoxes.length === 1) {
            const label = optionsContainer.querySelector(`label[for="${checkedBoxes[0].id}"]`);
            buttonTextElement.textContent = label ? label.textContent.trim() : "1 tag selected";
        } else {
            buttonTextElement.textContent = `${checkedBoxes.length} tags selected`;
        }
    }
}

export function toggleDropdown(config, show) {
    const { filterButtonId, dropdownId } = config;
    const filterButton = document.getElementById(filterButtonId);
    const tagFilterDropdown = document.getElementById(dropdownId);

    if (!filterButton || !tagFilterDropdown) return;

    const shouldBeOpen = typeof show === 'boolean' ? show : tagFilterDropdown.classList.contains('hidden');
    tagFilterDropdown.classList.toggle('hidden', !shouldBeOpen);
    filterButton.setAttribute('aria-expanded', String(shouldBeOpen));
}

export function clearTagSelection(config) {
    const { optionsContainerId, onClear } = config;
    const optionsContainer = document.getElementById(optionsContainerId);
    if (!optionsContainer) return;

    const checkedBoxes = optionsContainer.querySelectorAll('input[type="checkbox"]:checked');

    if (checkedBoxes.length > 0) {
        checkedBoxes.forEach(checkbox => {
            checkbox.checked = false;
        });
        if (typeof onClear === 'function') {
            onClear();
        }
    }
    toggleDropdown(config, false);
}