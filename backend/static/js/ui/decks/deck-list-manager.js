import { authFetch } from '../../auth/auth.js';
import { sortAndRenderDecks } from './sort-decks.js';

function getSelectedTagIds() {
    const tagFilterSelect = document.getElementById("filter-tags-select");
    const selectedIds = [];
    if (!tagFilterSelect) return selectedIds;

    for (const option of tagFilterSelect.options) {
        if (option.selected) {
            if (option.value && option.value !== "") {
                 selectedIds.push(option.value);
            }
        }
    }
    return selectedIds;
}

async function updateDeckListView() {
    const sortSelect = document.getElementById("sort_decks");
    const formatSelect = document.getElementById("filter_decks");
    const decksContainer = document.getElementById('decks-container');

    if (!sortSelect || !formatSelect || !decksContainer) {
        console.error("Missing required elements for updating deck list view.");
        return;
    }

    const sortValue = sortSelect.value;
    const formatValue = formatSelect.value;
    const selectedTagIds = getSelectedTagIds();

    const params = new URLSearchParams();
    if (formatValue && formatValue !== '0' && formatValue.toLowerCase() !== 'all') {
        params.append('deck_type_id', formatValue);
    }
    if (selectedTagIds.length > 0) {
        params.append('tags', selectedTagIds.join(','));
    }

    const apiUrl = `/api/user_decks?${params.toString()}`;
    decksContainer.innerHTML = '<p class="text-center text-gray-500 col-span-full">Loading decks...</p>';

    try {
        const response = await authFetch(apiUrl);
        if (!response) {
             throw new Error("Authentication or network error.");
        }
        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }

        const filteredDecks = await response.json();

        console.log('API response parsed:', filteredDecks);
        console.log(`Calling sortAndRenderDecks with:`, filteredDecks, `and sort option: ${sortValue}`);

        sortAndRenderDecks(filteredDecks || [], sortValue);

    } catch (error) {
        console.error("Error fetching or rendering decks:", error);
        if (typeof showFlashMessage === 'function') {
             showFlashMessage("Error loading decks. " + error.message, "danger");
        }
        if (decksContainer) {
            decksContainer.innerHTML = '<p class="text-red-500 col-span-full">Error loading decks.</p>';
        }
    }
}

export { updateDeckListView };

document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById("sort_decks") &&
        document.getElementById("filter_decks") &&
        document.getElementById("filter-tags-select"))
    {
        updateDeckListView();
    }
});