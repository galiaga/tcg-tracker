// backend/static/js/ui/tags/user-tags.js

// --- Imports ---
import {
    populateTagFilter,
    updateButtonText,
    toggleDropdown,
    clearTagSelection
} from '../tag-filter.js'; // Tag filter dropdown UI logic
import { authFetch } from '../../auth/auth.js'; // Authenticated fetch wrapper
import { sortAndRenderDecks } from '../decks/sort-decks.js'; // Renders deck cards
import { initializeMatchActionMenus } from '../matches/match-actions.js'; // Initializes match card menus (delete action)
import { handleRemoveMatchTagClick, displayMatches } from '../matches/match-list-manager.js'; // Renders match cards and handles tag removal from matches
import { openQuickAddTagModal, closeQuickAddTagModal, handleRemoveTagClick as handleRemoveDeckTagClick  } from '../tag-utils.js'; // Tag modal and deck tag removal logic

// --- Core Data Fetching and Display ---
async function fetchAndDisplayAssociatedItems() {
    const decksContainer = document.getElementById('associated-decks-list');
    const matchesContainer = document.getElementById('associated-matches-list');
    const optionsContainer = document.getElementById(pageFilterConfig.optionsContainerId); // Tag filter options container

    // Ensure required elements exist
    if (!decksContainer || !matchesContainer || !optionsContainer) {
        console.error("Containers for associated items or filter options not found!");
        return;
    }

    // Get selected tag IDs from the filter dropdown
    const selectedTagIds = Array.from(optionsContainer.querySelectorAll('input[type="checkbox"]:checked')).map(cb => cb.value);

    // Display message if no tags are selected
    if (selectedTagIds.length === 0) {
        decksContainer.innerHTML = '<p class="text-center text-violet-800 mt-4 p-4 text-base border border-dashed border-violet-300 rounded-lg md:col-span-2 xl:col-span-3">Select one or more tags above to view associated decks.</p>';
        matchesContainer.innerHTML = '<p class="text-center text-violet-800 mt-4 p-4 text-base border border-dashed border-violet-300 rounded-lg md:col-span-2 xl:col-span-3">Select one or more tags above to view associated matches.</p>';
        return;
    }

    // Set loading states
    decksContainer.innerHTML = '<p class="text-gray-500 italic text-sm">Loading decks...</p>';
    matchesContainer.innerHTML = '<p class="text-gray-500 italic text-sm">Loading matches...</p>';

    // Prepare query parameters for API calls
    const queryParams = selectedTagIds.length > 0 ? `?tags=${selectedTagIds.join(',')}` : '';

    try {
        // Fetch associated decks and matches concurrently
        const [decksResponse, matchesResponse] = await Promise.all([
            authFetch(`/api/user_decks${queryParams}`),
            authFetch(`/api/matches_history${queryParams}`)
        ]);

        // Process and display decks
        if (decksResponse.ok) {
            const decks = await decksResponse.json();
            sortAndRenderDecks(decks, null, decksContainer); // Render deck cards
            // Optional: Initialize deck action menus here if implemented
        } else {
            console.error("Failed to fetch decks:", decksResponse.status, await decksResponse.text().catch(()=>''));
            decksContainer.innerHTML = '<p class="text-red-500 text-sm">Error loading decks.</p>';
        }

        // Process and display matches
        if (matchesResponse.ok) {
            const matches = await matchesResponse.json();
            const noMatchesEl = null; // Define if you have a specific "no matches" element to toggle
            displayMatches(matches, matchesContainer, noMatchesEl); // Render match cards

            // Initialize action menus (like delete) for the displayed match cards
            if (matches && matches.length > 0) {
                // Pass the current function as a callback to refresh data after deletion
                initializeMatchActionMenus('associated-matches-list', fetchAndDisplayAssociatedItems);
            }

        } else {
            console.error("Failed to fetch matches:", matchesResponse.status, await matchesResponse.text().catch(()=>''));
            matchesContainer.innerHTML = '<p class="text-red-500 text-sm">Error loading matches.</p>';
        }

    } catch (error) {
        // Handle general fetch errors
        console.error("Error fetching associated items:", error);
        decksContainer.innerHTML = '<p class="text-red-500 text-sm">Error loading decks.</p>';
        matchesContainer.innerHTML = '<p class="text-red-500 text-sm">Error loading matches.</p>';
    }
}

// --- Tag Filter Configuration ---
const pageFilterConfig = {
    optionsContainerId: 'tag-filter-options',
    filterButtonId: 'tag-filter-button',
    buttonTextElementId: 'tag-filter-button-text',
    clearButtonId: 'clear-tag-filter-button',
    dropdownId: 'tag-filter-dropdown',
    checkboxName: 'page_tag_filter',
    checkboxIdPrefix: 'page-tag-filter',
    buttonDefaultText: "Select Tags to View",
    // Define actions when the filter changes or is cleared
    onFilterChange: () => {
        updateButtonText(pageFilterConfig);
        fetchAndDisplayAssociatedItems(); // Refresh lists when filter changes
    },
    onClear: () => {
        updateButtonText(pageFilterConfig);
        fetchAndDisplayAssociatedItems(); // Refresh lists when filter is cleared
    }
};

// --- DOMContentLoaded Initialization ---
document.addEventListener("DOMContentLoaded", () => {

    // Get references to essential UI elements
    const filterButton = document.getElementById(pageFilterConfig.filterButtonId);
    const clearButton = document.getElementById(pageFilterConfig.clearButtonId);
    const dropdown = document.getElementById(pageFilterConfig.dropdownId);
    const decksContainer = document.getElementById('associated-decks-list');
    const matchesContainer = document.getElementById('associated-matches-list');
    const quickAddModal = document.getElementById("quickAddTagModal");
    const quickAddModalCloseBtn = document.getElementById("quickAddTagModalCloseButton");

    // Check if filter elements are present
    if (!filterButton || !clearButton || !dropdown) {
        console.error("Error: Essential filter UI elements not found on tags page.");
        return;
    }

    // Initialize the tag filter dropdown
    populateTagFilter(pageFilterConfig);
    updateButtonText(pageFilterConfig); // Set initial button text

    // Add event listeners for the tag filter dropdown
    filterButton.addEventListener('click', (e) => {
        e.stopPropagation();
        toggleDropdown(pageFilterConfig);
    });

    clearButton.addEventListener('click', (e) => {
        e.stopPropagation();
        clearTagSelection(pageFilterConfig);
    });

    // Close dropdown if clicked outside
    document.addEventListener('click', (event) => {
        if (dropdown && !dropdown.classList.contains('hidden') &&
            !filterButton.contains(event.target) &&
            !dropdown.contains(event.target))
        {
            toggleDropdown(pageFilterConfig, false);
        }
    });

    // Setup event listeners for interactions within the deck list container
    if (decksContainer) {
        decksContainer.addEventListener('click', (event) => {
            const removeBtn = event.target.closest('.remove-tag-button'); // Check for deck tag removal button
            const addBtn = event.target.closest('.add-deck-tag-button'); // Check for deck tag add button

            // Handle removing a tag from a deck card
            if (removeBtn && typeof handleRemoveDeckTagClick === 'function') {
                handleRemoveDeckTagClick(event).then(() => {
                    fetchAndDisplayAssociatedItems(); // Refresh lists after tag removal
                }).catch(err => console.error("Error removing deck tag:", err));
            }
            // Handle adding a tag to a deck card (opens modal)
            else if (addBtn) {
                event.preventDefault();
                event.stopPropagation();
                const deckId = addBtn.dataset.deckId;
                if (deckId && typeof openQuickAddTagModal === 'function') {
                    // Pass refresh function as callback for the modal
                    openQuickAddTagModal(deckId, 'deck', fetchAndDisplayAssociatedItems);
                } else {
                    console.error("Could not open add tag modal for deck:", deckId);
                }
            }
        });
    } else {
        console.warn("Container #associated-decks-list not found for attaching card listeners.");
    }

    // Setup event listeners for interactions within the match list container
    // Note: This handles direct tag add/remove buttons, not the menu actions
    if (matchesContainer) {
        matchesContainer.addEventListener('click', (event) => {
            const removeBtn = event.target.closest('.remove-match-tag-button'); // Check for match tag removal button
            const addBtn = event.target.closest('.add-match-tag-button'); // Check for match tag add button

            // Handle removing a tag from a match card
            if (removeBtn && typeof handleRemoveMatchTagClick === 'function') {
                handleRemoveMatchTagClick(event).then(() => {
                    fetchAndDisplayAssociatedItems(); // Refresh lists after tag removal
                }).catch(err => console.error("Error removing match tag:", err));
            }
            // Handle adding a tag to a match card (opens modal)
            else if (addBtn) {
                event.preventDefault();
                event.stopPropagation();
                const matchId = addBtn.dataset.matchId;
                if (matchId && typeof openQuickAddTagModal === 'function') {
                    // Pass refresh function as callback for the modal
                    openQuickAddTagModal(matchId, 'match', fetchAndDisplayAssociatedItems);
                } else {
                    console.error("Could not open add tag modal for match:", matchId);
                }
            }
            // Match menu actions (like delete) are initialized separately by initializeMatchActionMenus
        });
    } else {
        console.warn("Container #associated-matches-list not found for attaching card listeners.");
    }

    // Setup listeners for the Quick Add Tag modal
    if (quickAddModal && quickAddModalCloseBtn && typeof closeQuickAddTagModal === 'function') {
        quickAddModalCloseBtn.addEventListener('click', closeQuickAddTagModal);
        // Close modal if background is clicked
        quickAddModal.addEventListener('click', (event) => {
            if (event.target === quickAddModal) {
                closeQuickAddTagModal();
            }
        });
    }

    // Initial fetch of data when the page loads (if any tags are pre-selected or default behavior requires it)
    // Consider if an initial fetch is always needed or only after first filter interaction
    // fetchAndDisplayAssociatedItems(); // Uncomment if you want an initial load based on default filter state

}); // End DOMContentLoaded