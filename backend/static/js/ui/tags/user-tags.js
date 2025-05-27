// backend/static/js/ui/tags/user-tags.js

// --- Imports ---
// REMOVE old filter imports: import { populateTagFilter, updateButtonText, toggleDropdown, clearTagSelection } from '../tag-filter.js';
import { authFetch } from '../../auth/auth.js'; // Authenticated fetch wrapper
import { sortAndRenderDecks } from '../decks/sort-decks.js'; // Renders deck cards
import { initializeMatchActionMenus } from '../matches/match-actions.js'; // Initializes match card menus (delete action)
import { handleRemoveMatchTagClick, displayMatches } from '../matches/match-list-manager.js'; // Renders match cards and handles tag removal from matches
import { openQuickAddTagModal, closeQuickAddTagModal, handleRemoveTagClick as handleRemoveDeckTagClick  } from '../tag-utils.js'; // Tag modal and deck tag removal logic

// --- Global State ---
let allUserTags = []; // Store all fetched tags for searching
let selectedTagIds = new Set(); // Use a Set for efficient add/delete/check

// --- DOM Element References ---
const decksContainer = document.getElementById('associated-decks-list');
const matchesContainer = document.getElementById('associated-matches-list');
const recentTagsContainer = document.getElementById('recent-tags-container');
const tagSearchInput = document.getElementById('tag-search-input');
const tagSearchResultsContainer = document.getElementById('tag-search-results');
const selectedTagsDisplay = document.getElementById('selected-tags-display');
const noTagsSelectedText = document.getElementById('no-tags-selected-text');
const clearAllTagsButton = document.getElementById('clear-all-tags-button');
const quickAddModal = document.getElementById("quickAddTagModal");
const quickAddModalCloseBtn = document.getElementById("quickAddTagModalCloseButton");
const selectedTagsRow = document.getElementById('selected-tags-row');

// --- Core Data Fetching and Display ---

/**
 * Fetches decks and matches associated with the currently selected tags.
 */
async function fetchAndDisplayAssociatedItems() {
    // Ensure required elements exist
    if (!decksContainer || !matchesContainer) {
        console.error("Containers for associated items not found!");
        return;
    }

    const currentSelectedIds = Array.from(selectedTagIds);

    // Display message if no tags are selected
    if (currentSelectedIds.length === 0) {
        decksContainer.innerHTML = '<p class="text-center text-gray-900 dark:text-violet-300 mt-4 p-4 text-base border border-dashed border-violet-300 rounded-lg md:col-span-2 xl:col-span-3">Select one or more tags above to view associated decks.</p>';
        matchesContainer.innerHTML = '<p class="text-center text-gray-900 dark:text-violet-300 mt-4 p-4 text-base border border-dashed border-violet-300 rounded-lg md:col-span-2 xl:col-span-3">Select one or more tags above to view associated matches.</p>';
        return;
    }

    // Set loading states
    decksContainer.innerHTML = '<p class="text-gray-500 italic text-sm">Loading decks...</p>';
    matchesContainer.innerHTML = '<p class="text-gray-500 italic text-sm">Loading matches...</p>';

    // Prepare query parameters for API calls
    const queryParams = `?tags=${currentSelectedIds.join(',')}`;

    try {
        // Fetch associated decks and matches concurrently
        const [decksResponse, matchesResponse] = await Promise.all([
            authFetch(`/api/user_decks${queryParams}`),
            authFetch(`/api/matches_history${queryParams}`) // Assuming this endpoint can filter by tags
        ]);

        // Process and display decks
        if (decksResponse.ok) {
            const decks = await decksResponse.json();
            sortAndRenderDecks(decks, null, decksContainer); // Render deck cards
            // Add listeners for add/remove tag buttons *within* the deck cards
            setupDeckCardTagListeners();
        } else {
            console.error("Failed to fetch decks:", decksResponse.status, await decksResponse.text().catch(()=>''));
            decksContainer.innerHTML = '<p class="text-red-500 text-sm">Error loading decks.</p>';
        }

        // Process and display matches
        if (matchesResponse.ok) {
            const matches = await matchesResponse.json();
            const noMatchesEl = null; // Define if you have a specific "no matches" element to toggle
            displayMatches(matches, matchesContainer, noMatchesEl); // Render match cards using the function from match-list-manager
             // Add listeners for add/remove tag buttons *within* the match cards
            setupMatchCardTagListeners();

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

// --- Tag Selection UI ---

/**
 * Creates the HTML for a single tag chip.
 * @param {object} tag - The tag object {id, name}.
 * @param {boolean} isSelected - Whether the tag is currently selected.
 * @param {boolean} isInteractive - If true, adds click listener for selection.
 * @param {boolean} showRemoveIcon - If true, shows a remove (x) icon (for selected tags display).
 * @returns {string} - HTML string for the tag chip.
 */
function createTagChipHtml(tag, isSelected = false, isInteractive = true, showRemoveIcon = false) {
    const selectedClass = isSelected ? 'bg-violet-600 text-white hover:bg-violet-700' : 'bg-violet-100 text-violet-800 hover:bg-violet-200';
    const interactiveClass = isInteractive ? 'cursor-pointer' : '';
    const removeIconHtml = showRemoveIcon ?
        `<button type="button" class="tag-remove-from-selected ml-1 -mr-0.5 rounded-full inline-flex items-center justify-center text-violet-200 hover:text-white focus:outline-none" data-tag-id="${tag.id}" aria-label="Remove tag ${tag.name}">
            <svg class="h-3.5 w-3.5" stroke="currentColor" fill="none" viewBox="0 0 8 8"><path stroke-linecap="round" stroke-width="1.5" d="M1 1l6 6m0-6L1 7" /></svg>
         </button>` : '';

    return `
        <span class="tag-chip inline-flex items-center px-2.5 py-1 rounded-full text-sm font-medium ${selectedClass} ${interactiveClass} transition-colors duration-150"
              data-tag-id="${tag.id}"
              data-tag-name="${tag.name}"
              role="button"
              tabindex="0"
              aria-pressed="${isSelected}">
            ${tag.name}
            ${removeIconHtml}
        </span>
    `;
}

/**
 * Renders tag chips into a specified container.
 * @param {Array<object>} tags - Array of tag objects {id, name}.
 * @param {HTMLElement} container - The container element to render into.
 * @param {boolean} isInteractive - Whether the chips should be clickable for selection.
 */
function renderTagChips(tags, container, isInteractive = true) {
    if (!container) return;
    container.innerHTML = ''; // Clear previous content
    if (!tags || tags.length === 0) {
        container.innerHTML = `<p class="text-sm text-gray-500 italic w-full">No tags found.</p>`;
        return;
    }
    const fragment = document.createDocumentFragment();
    tags.forEach(tag => {
        const isSelected = selectedTagIds.has(tag.id.toString());
        const chipHtml = createTagChipHtml(tag, isSelected, isInteractive, false); // Don't show remove icon here
        const chipElement = document.createElement('div'); // Create a temporary div to parse HTML
        chipElement.innerHTML = chipHtml.trim();
        fragment.appendChild(chipElement.firstChild);
    });
    container.appendChild(fragment);
}

/**
 * Updates the display area showing currently selected tags.
 */
function updateSelectedTagsDisplay() {
    // Check if all required elements exist
    if (!selectedTagsDisplay || !noTagsSelectedText || !clearAllTagsButton || !selectedTagsRow) {
        console.warn("Missing elements for updating selected tags display.");
        return;
    }

    selectedTagsDisplay.innerHTML = ''; // Clear existing chips

    if (selectedTagIds.size === 0) {
        // STATE: No tags selected
        selectedTagsDisplay.appendChild(noTagsSelectedText);
        noTagsSelectedText.classList.remove('hidden');
        clearAllTagsButton.classList.add('hidden'); // Hide button

        // Adjust alignment: Center label with empty field
        selectedTagsRow.classList.remove('items-start');
        selectedTagsRow.classList.add('items-center');

    } else {
        // STATE: One or more tags selected
        noTagsSelectedText.classList.add('hidden');
        const fragment = document.createDocumentFragment();
        selectedTagIds.forEach(tagId => {
            const tag = allUserTags.find(t => t.id.toString() === tagId);
            if (tag) {
                const chipHtml = createTagChipHtml(tag, true, false, true);
                const chipElement = document.createElement('div');
                chipElement.innerHTML = chipHtml.trim();
                fragment.appendChild(chipElement.firstChild);
            }
        });
        selectedTagsDisplay.appendChild(fragment);
        clearAllTagsButton.classList.remove('hidden'); // Show button

        // Adjust alignment: Align label/button column top with tag area top
        selectedTagsRow.classList.remove('items-center');
        selectedTagsRow.classList.add('items-start');
    }

    // Re-apply listener for remove buttons within the selected display (if needed, depends on how it's set up)
    // If using delegation on selectedTagsDisplay container, this might not be needed here.
    // setupSelectedTagRemoveListeners(); // Call if necessary
}


/**
 * Toggles the selection state of a tag.
 * @param {string} tagId - The ID of the tag to toggle.
 */
function toggleTagSelection(tagId) {
    if (selectedTagIds.has(tagId)) {
        selectedTagIds.delete(tagId);
    } else {
        selectedTagIds.add(tagId);
    }
    // Update visuals
    updateTagChipAppearance(tagId);
    updateSelectedTagsDisplay();
    // Fetch new data
    fetchAndDisplayAssociatedItems();
}

/**
 * Updates the visual appearance of a specific tag chip across all sections (recent, search results).
 * @param {string} tagId - The ID of the tag chip to update.
 */
function updateTagChipAppearance(tagId) {
    let chipsToUpdate;

    if (tagId) {
        // Select specific chips if tagId is provided
        chipsToUpdate = document.querySelectorAll(
            `#recent-tags-container .tag-chip[data-tag-id="${tagId}"],
             #tag-search-results .tag-chip[data-tag-id="${tagId}"]`
        );
    } else {
        // Select ALL chips in the interactive areas if no tagId (for reset)
        chipsToUpdate = document.querySelectorAll(
            `#recent-tags-container .tag-chip,
             #tag-search-results .tag-chip`
        );
    }


    chipsToUpdate.forEach(chip => {
        // Determine the correct selected state ONLY if we are updating a specific tag.
        // If tagId is null/undefined, we force isSelected to false (resetting).
        const currentTagId = chip.dataset.tagId;
        const isSelected = tagId ? selectedTagIds.has(currentTagId) : false;

        chip.setAttribute('aria-pressed', isSelected);
        // Apply classes based on the determined selected state
        chip.classList.toggle('bg-violet-600', isSelected);
        chip.classList.toggle('text-white', isSelected);
        chip.classList.toggle('hover:bg-violet-700', isSelected);
        chip.classList.toggle('bg-violet-100', !isSelected);
        chip.classList.toggle('text-violet-800', !isSelected);
        chip.classList.toggle('hover:bg-violet-200', !isSelected);
    });
}


// --- Event Handlers ---

/**
 * Handles clicks on tag chips in the Recent or Search Results sections.
 * @param {Event} event - The click event.
 */
function handleTagChipClick(event) {
    const chip = event.target.closest('.tag-chip');
    if (chip && chip.dataset.tagId) {
        event.preventDefault();
        event.stopPropagation();
        toggleTagSelection(chip.dataset.tagId);
    }
}

/**
 * Handles clicks on the remove 'x' button within the Selected Tags display area.
 * @param {Event} event - The click event.
 */
function handleRemoveSelectedTagClick(event) {
    const removeButton = event.target.closest('.tag-remove-from-selected');
   if (removeButton && removeButton.dataset.tagId) {
       event.preventDefault();
       event.stopPropagation();
       const tagIdToRemove = removeButton.dataset.tagId;
       // Toggle selection (which removes it from the Set)
       selectedTagIds.delete(tagIdToRemove); // Directly delete, toggle is not needed here
       // Update visuals
       updateTagChipAppearance(tagIdToRemove); // Update the appearance of the removed tag's chips
       updateSelectedTagsDisplay(); // Update the selected tags area
       // Fetch new data
       fetchAndDisplayAssociatedItems();
   }
}

/**
 * Handles input in the tag search box, filtering and displaying results.
 * @param {Event} event - The input event.
 */
function handleTagSearchInput(event) {
    const searchTerm = event.target.value.toLowerCase().trim();
    if (!tagSearchResultsContainer) return;

    if (!searchTerm) {
        tagSearchResultsContainer.innerHTML = ''; // Clear results if search is empty
        return;
    }

    const filteredTags = allUserTags.filter(tag =>
        tag.name.toLowerCase().includes(searchTerm) &&
        !selectedTagIds.has(tag.id.toString()) // Optionally hide already selected tags from search results
    );

    renderTagChips(filteredTags, tagSearchResultsContainer, true); // Render results as interactive chips
}

/**
 * Clears all selected tags.
 */
function clearAllTagSelections() {
    const previouslySelected = new Set(selectedTagIds); // Keep track of what *was* selected
    selectedTagIds.clear();

    // Update the appearance of chips that *were* selected
    previouslySelected.forEach(tagId => {
         updateTagChipAppearance(tagId); // Update specific chips that changed state
    });
    // Or simpler if the modified updateTagChipAppearance works for reset:
    // updateTagChipAppearance(); // Reset all chips in interactive areas

    updateSelectedTagsDisplay(); // Update the "Selected Tags:" area
    fetchAndDisplayAssociatedItems(); // Fetch results for no tags
    if(tagSearchInput) tagSearchInput.value = ''; // Clear search input
    if(tagSearchResultsContainer) tagSearchResultsContainer.innerHTML = ''; // Clear search results
}

// --- Initialization ---

/**
 * Fetches all user tags from the API.
 */
async function fetchAllUserTags() {
    try {
        const response = await authFetch('/api/tags'); // Adjust endpoint if needed
        if (!response.ok) {
            throw new Error(`Failed to fetch tags: ${response.status}`);
        }
        allUserTags = await response.json();
        // Sort tags alphabetically for consistent display in search/all
        allUserTags.sort((a, b) => a.name.localeCompare(b.name));
        return allUserTags;
    } catch (error) {
        console.error("Error fetching user tags:", error);
        if (recentTagsContainer) recentTagsContainer.innerHTML = '<p class="text-sm text-red-500 italic w-full">Could not load tags.</p>';
        return []; // Return empty array on error
    }
}

/**
 * Sets up event listeners for tag chips in the results lists (decks/matches).
 * These listeners handle adding/removing tags *from* specific items.
 */
function setupDeckCardTagListeners() {
     if (decksContainer) {
         // Remove previous listeners to avoid duplicates if re-rendering
        decksContainer.removeEventListener('click', handleDeckCardInteraction);
        // Add new listener
        decksContainer.addEventListener('click', handleDeckCardInteraction);
    }
}
function handleDeckCardInteraction(event) {
    const removeBtn = event.target.closest('.remove-tag-button'); // Check for deck tag removal button
    const addBtn = event.target.closest('.add-deck-tag-button'); // Check for deck tag add button

    if (removeBtn && typeof handleRemoveDeckTagClick === 'function') {
        handleRemoveDeckTagClick(event).then(() => {
            // Only refresh if the removed tag was one of the selected filter tags
            const removedTagId = removeBtn.closest('.tag-pill')?.dataset.tagId;
            if (removedTagId && selectedTagIds.has(removedTagId)) {
                 fetchAndDisplayAssociatedItems();
            } else {
                // If the removed tag wasn't part of the filter, maybe just remove the pill visually?
                // Or still refresh to be safe, as backend state changed. Let's refresh.
                fetchAndDisplayAssociatedItems();
            }
        }).catch(err => console.error("Error removing deck tag:", err));
    }
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
}

function setupMatchCardTagListeners() {
    if (matchesContainer) {
        // Remove previous listeners to avoid duplicates
        matchesContainer.removeEventListener('click', handleMatchCardInteraction);
        // Add new listener
        matchesContainer.addEventListener('click', handleMatchCardInteraction);
    }
}
function handleMatchCardInteraction(event) {
    const removeBtn = event.target.closest('.remove-match-tag-button'); // Check for match tag removal button
    const addBtn = event.target.closest('.add-match-tag-button'); // Check for match tag add button

    if (removeBtn && typeof handleRemoveMatchTagClick === 'function') {
        handleRemoveMatchTagClick(event).then(() => {
             // Similar logic as decks: refresh if the removed tag was part of the filter
            const removedTagId = removeBtn.closest('.tag-pill')?.dataset.tagId;
             if (removedTagId && selectedTagIds.has(removedTagId)) {
                 fetchAndDisplayAssociatedItems();
            } else {
                 fetchAndDisplayAssociatedItems(); // Refresh anyway for consistency
            }
        }).catch(err => console.error("Error removing match tag:", err));
    }
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
    // Note: Clicks on the match options menu (delete) are handled by initializeMatchActionMenus
}

/**
 * Sets up event listeners for the remove 'x' buttons in the selected tags display.
 * Needs to be called after updateSelectedTagsDisplay.
 */
function setupSelectedTagRemoveListeners() {
    if (selectedTagsDisplay) {
        // Use event delegation on the container
        selectedTagsDisplay.removeEventListener('click', handleRemoveSelectedTagClick); // Prevent duplicates
        selectedTagsDisplay.addEventListener('click', handleRemoveSelectedTagClick);
    }
}


document.addEventListener("DOMContentLoaded", async () => {
    // Ensure essential containers exist
    if (!recentTagsContainer || !tagSearchInput || !tagSearchResultsContainer || !selectedTagsDisplay || !clearAllTagsButton) {
        console.error("Error: Essential tag selection UI elements not found.");
        return;
    }

    // 1. Fetch all tags
    await fetchAllUserTags();

    // 2. Display Recent Tags (e.g., first 5-7 tags, assuming API doesn't sort by recency yet)
    const recentTagsToShow = allUserTags.slice(0, 5); // Adjust count as needed
    renderTagChips(recentTagsToShow, recentTagsContainer, true);

    // 3. Setup Event Listeners for Tag Selection
    recentTagsContainer.addEventListener('click', handleTagChipClick);
    tagSearchResultsContainer.addEventListener('click', handleTagChipClick);
    tagSearchInput.addEventListener('input', handleTagSearchInput);
    clearAllTagsButton.addEventListener('click', clearAllTagSelections);
    // Listener for remove buttons in selected area is set up after updates

    // 4. Setup listeners for interactions within the results lists (delegated)
    setupDeckCardTagListeners();
    setupMatchCardTagListeners(); // Setup initially, will be re-applied after fetch

    // 5. Setup listeners for the Quick Add Tag modal (if elements exist)
    if (quickAddModal && quickAddModalCloseBtn && typeof closeQuickAddTagModal === 'function') {
        quickAddModalCloseBtn.addEventListener('click', closeQuickAddTagModal);
        quickAddModal.addEventListener('click', (event) => {
            if (event.target === quickAddModal) {
                closeQuickAddTagModal();
            }
        });
    }

    // 6. Initial state update
    updateSelectedTagsDisplay(); // Show "No tags selected" initially
    fetchAndDisplayAssociatedItems(); // Show initial placeholder messages in results areas

}); // End DOMContentLoaded