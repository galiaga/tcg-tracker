import {
    populateTagFilter,
    updateButtonText,
    toggleDropdown,
    clearTagSelection
} from '../tag-filter.js';
import { authFetch } from '../../auth/auth.js';
import { sortAndRenderDecks } from '../decks/sort-decks.js';

import { displayMatches, handleRemoveMatchTagClick } from '../matches/match-list-manager.js';
import { handleRemoveTagClick as handleRemoveDeckTagClick } from '../decks/deck-list-manager.js'; 
import { openQuickAddTagModal, closeQuickAddTagModal } from '../tag-utils.js'; 

async function fetchAndDisplayAssociatedItems() {
    const decksContainer = document.getElementById('associated-decks-list');
    const matchesContainer = document.getElementById('associated-matches-list');
    const optionsContainer = document.getElementById(pageFilterConfig.optionsContainerId);

    if (!decksContainer || !matchesContainer || !optionsContainer) {
        console.error("Containers for associated items or filter options not found!");
        return;
    }

    const selectedTagIds = Array.from(optionsContainer.querySelectorAll('input[type="checkbox"]:checked')).map(cb => cb.value);

    decksContainer.innerHTML = '<p class="text-gray-500 italic text-sm">Loading decks...</p>';
    matchesContainer.innerHTML = '<p class="text-gray-500 italic text-sm">Loading matches...</p>';

    const queryParams = selectedTagIds.length > 0 ? `?tags=${selectedTagIds.join(',')}` : '';

    try {
        const [decksResponse, matchesResponse] = await Promise.all([
            authFetch(`/api/user_decks${queryParams}`),
            authFetch(`/api/matches_history${queryParams}`)
        ]);

        if (decksResponse.ok) {
            const decks = await decksResponse.json();
            sortAndRenderDecks(decks, null, decksContainer);
        } else {
            console.error("Failed to fetch decks:", decksResponse.status, await decksResponse.text().catch(()=>''));
            decksContainer.innerHTML = '<p class="text-red-500 text-sm">Error loading decks.</p>';
        }

        if (matchesResponse.ok) {
            const matches = await matchesResponse.json();
            const noMatchesEl = null;
            displayMatches(matches, matchesContainer, noMatchesEl);
        } else {
            console.error("Failed to fetch matches:", matchesResponse.status, await matchesResponse.text().catch(()=>''));
            matchesContainer.innerHTML = '<p class="text-red-500 text-sm">Error loading matches.</p>';
        }

    } catch (error) {
        console.error("Error fetching associated items:", error);
        decksContainer.innerHTML = '<p class="text-red-500 text-sm">Error loading decks.</p>';
        matchesContainer.innerHTML = '<p class="text-red-500 text-sm">Error loading matches.</p>';
    }
}

const pageFilterConfig = {
    optionsContainerId: 'tag-filter-options',
    filterButtonId: 'tag-filter-button',
    buttonTextElementId: 'tag-filter-button-text',
    clearButtonId: 'clear-tag-filter-button',
    dropdownId: 'tag-filter-dropdown',
    checkboxName: 'page_tag_filter',
    checkboxIdPrefix: 'page-tag-filter',
    buttonDefaultText: "Select Tags to View",
    onFilterChange: () => {
        updateButtonText(pageFilterConfig);
        fetchAndDisplayAssociatedItems();
    },
    onClear: () => {
        updateButtonText(pageFilterConfig);
        fetchAndDisplayAssociatedItems();
    }
};

document.addEventListener("DOMContentLoaded", () => {

    const filterButton = document.getElementById(pageFilterConfig.filterButtonId);
    const clearButton = document.getElementById(pageFilterConfig.clearButtonId);
    const dropdown = document.getElementById(pageFilterConfig.dropdownId);
    const decksContainer = document.getElementById('associated-decks-list');
    const matchesContainer = document.getElementById('associated-matches-list');
    const quickAddModal = document.getElementById("quickAddTagModal");
    const quickAddModalCloseBtn = document.getElementById("quickAddTagModalCloseButton");

    if (!filterButton || !clearButton || !dropdown) {
        console.error("Error: Essential filter UI elements not found on tags page.");
        return;
    }

    populateTagFilter(pageFilterConfig);
    updateButtonText(pageFilterConfig);

    filterButton.addEventListener('click', (e) => {
        e.stopPropagation();
        toggleDropdown(pageFilterConfig);
    });

    clearButton.addEventListener('click', (e) => {
        e.stopPropagation();
        clearTagSelection(pageFilterConfig);
    });

    document.addEventListener('click', (event) => {
        if (dropdown && !dropdown.classList.contains('hidden') &&
            !filterButton.contains(event.target) &&
            !dropdown.contains(event.target))
        {
            toggleDropdown(pageFilterConfig, false);
        }
    });

    if (decksContainer) {
        decksContainer.addEventListener('click', (event) => {
            const removeBtn = event.target.closest('.remove-tag-button');
            const addBtn = event.target.closest('.add-deck-tag-button');

            if (removeBtn && typeof handleRemoveDeckTagClick === 'function') {
                handleRemoveDeckTagClick(event).then(() => {
                    fetchAndDisplayAssociatedItems();
                }).catch(err => console.error("Error removing deck tag:", err));
            } else if (addBtn) {
                event.preventDefault();
                event.stopPropagation();
                const deckId = addBtn.dataset.deckId;
                if (deckId && typeof openQuickAddTagModal === 'function') {
                    openQuickAddTagModal(deckId, 'deck', fetchAndDisplayAssociatedItems);
                } else {
                    console.error("Could not open add tag modal for deck:", deckId);
                }
            }
        });
    } else {
        console.warn("Container #associated-decks-list not found for attaching card listeners.");
    }

    if (matchesContainer) {
        matchesContainer.addEventListener('click', (event) => {
            const removeBtn = event.target.closest('.remove-match-tag-button');
            const addBtn = event.target.closest('.add-match-tag-button');

            if (removeBtn && typeof handleRemoveMatchTagClick === 'function') {
                handleRemoveMatchTagClick(event).then(() => {
                    fetchAndDisplayAssociatedItems();
                }).catch(err => console.error("Error removing match tag:", err));
            } else if (addBtn) {
                event.preventDefault();
                event.stopPropagation();
                const matchId = addBtn.dataset.matchId;
                if (matchId && typeof openQuickAddTagModal === 'function') {
                    openQuickAddTagModal(matchId, 'match', fetchAndDisplayAssociatedItems);
                } else {
                    console.error("Could not open add tag modal for match:", matchId);
                }
            }
        });
    } else {
        console.warn("Container #associated-matches-list not found for attaching card listeners.");
    }

    if (quickAddModal && quickAddModalCloseBtn && typeof closeQuickAddTagModal === 'function') {
        quickAddModalCloseBtn.addEventListener('click', closeQuickAddTagModal);
        quickAddModal.addEventListener('click', (event) => {
            if (event.target === quickAddModal) {
                closeQuickAddTagModal();
            }
        });
    }

});