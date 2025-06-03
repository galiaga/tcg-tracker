// backend/static/js/ui/tags/user-tags.js

// --- Imports ---
import { authFetch } from '../../auth/auth.js';
import { renderDeckCard, renderEmptyDecksMessage as renderEmptyAssociatedDecksMessage } from '../decks/deckCardComponent.js';
import { displayMatches as renderAssociatedMatches, handleRemoveMatchTagClick } from '../matches/match-list-manager.js';
import { initializeMatchActionMenus } from '../matches/match-actions.js';
import { openQuickAddTagModal, closeQuickAddTagModal, handleRemoveTagClick as handleRemoveDeckTagClick } from '../tag-utils.js';

// --- Global State ---
let allUserTags = [];
let selectedTagIds = new Set();

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
const quickAddModalDoneBtn = document.getElementById("quickAddTagModalDoneButton");
const selectedTagsRow = document.getElementById('selected-tags-row');


// --- Placeholder for Search Results ---
const searchResultsPlaceholderHtml = '<p class="text-xs text-center text-gray-400 dark:text-gray-500 p-2 italic">Start typing to search tags.</p>';

// --- Core Data Fetching and Display ---
async function fetchAndDisplayAssociatedItems() {
    if (!decksContainer || !matchesContainer) {
        console.error("[user-tags.js] Containers for associated items not found!");
        return;
    }

    const currentSelectedIdsArray = Array.from(selectedTagIds);
    const noTagsSelectedMessageDecks = '<p class="text-center text-gray-700 dark:text-gray-300 mt-4 p-4 text-base border border-dashed border-gray-300 dark:border-gray-600 rounded-lg md:col-span-full">Select one or more tags above to view associated decks.</p>';
    const noTagsSelectedMessageMatches = '<p class="text-center text-gray-700 dark:text-gray-300 mt-4 p-4 text-base border border-dashed border-gray-300 dark:border-gray-600 rounded-lg md:col-span-full">Select one or more tags above to view associated matches.</p>';


    if (currentSelectedIdsArray.length === 0) {
        decksContainer.innerHTML = noTagsSelectedMessageDecks;
        matchesContainer.innerHTML = noTagsSelectedMessageMatches;
        return;
    }

    decksContainer.innerHTML = '<p class="text-gray-500 dark:text-gray-400 italic text-sm p-4 md:col-span-full">Loading associated decks...</p>';
    matchesContainer.innerHTML = '<p class="text-gray-500 dark:text-gray-400 italic text-sm p-4 md:col-span-full">Loading associated matches...</p>';

    const queryParams = `?tags=${currentSelectedIdsArray.join(',')}`;

    try {
        const [decksResponse, matchesResponse] = await Promise.all([
            authFetch(`/api/user_decks${queryParams}`),
            authFetch(`/api/matches_history${queryParams}`)
        ]);

        // Process and display decks
        if (decksResponse.ok) {
            const decks = await decksResponse.json();
            if (decks && decks.length > 0) {
                decksContainer.innerHTML = ''; // Clear loading
                const fragment = document.createDocumentFragment();
                decks.forEach(deck => {
                    const deckCardElement = renderDeckCard(deck, fetchAndDisplayAssociatedItems);
                    fragment.appendChild(deckCardElement);
                });
                decksContainer.appendChild(fragment);
            } else {
                renderEmptyAssociatedDecksMessage(decksContainer, "No decks found with the selected tags.");
            }
            setupDeckCardTagListeners();
        } else {
            console.error("Failed to fetch decks:", decksResponse.status);
            decksContainer.innerHTML = '<p class="text-red-500 dark:text-red-400 text-sm p-4 md:col-span-full">Error loading decks.</p>';
        }

        // Process and display matches
        if (matchesResponse.ok) {
            const matches = await matchesResponse.json();
            const noMatchesPlaceholder = document.createElement('div'); 
            if (matches && matches.length > 0) {
                matchesContainer.innerHTML = ''; 
                renderAssociatedMatches(matches, matchesContainer, noMatchesPlaceholder, fetchAndDisplayAssociatedItems);
                initializeMatchActionMenus('associated-matches-list', fetchAndDisplayAssociatedItems);
            } else {
                matchesContainer.innerHTML = '<p class="text-center text-gray-700 dark:text-gray-300 mt-4 p-4 text-base border border-dashed border-gray-300 dark:border-gray-600 rounded-lg md:col-span-full">No matches found with the selected tags.</p>';
            }
            setupMatchCardTagListeners();
        } else {
            console.error("Failed to fetch matches:", matchesResponse.status);
            matchesContainer.innerHTML = '<p class="text-red-500 dark:text-red-400 text-sm p-4 md:col-span-full">Error loading matches.</p>';
        }

    } catch (error) {
        console.error("Error fetching associated items:", error);
        decksContainer.innerHTML = '<p class="text-red-500 dark:text-red-400 text-sm p-4 md:col-span-full">Error loading associated items.</p>';
        matchesContainer.innerHTML = '<p class="text-red-500 dark:text-red-400 text-sm p-4 md:col-span-full">Error loading associated items.</p>';
    }
}


// --- Tag Selection UI ---
function createTagChipHtml(tag, isSelected = false, isInteractive = true, showRemoveIcon = false) {
    const baseClasses = "inline-flex items-center px-3 py-1.5 rounded-full text-sm font-medium transition-colors duration-150";
    const selectedStateClasses = "bg-violet-600 text-white hover:bg-violet-700 dark:bg-violet-500 dark:hover:bg-violet-400";
    const unselectedStateClasses = "bg-violet-100 text-violet-700 hover:bg-violet-200 dark:bg-slate-700 dark:text-violet-300 dark:hover:bg-slate-600";
    const stateClasses = isSelected ? selectedStateClasses : unselectedStateClasses;
    const interactiveClass = isInteractive ? 'cursor-pointer' : '';

    const removeIconHtml = showRemoveIcon ?
        `<button type="button" class="tag-remove-from-selected ml-1.5 -mr-1 p-0.5 rounded-full inline-flex items-center justify-center text-violet-200 hover:text-white focus:outline-none focus:bg-violet-700 dark:focus:bg-violet-600" data-tag-id="${tag.id}" aria-label="Remove tag ${tag.name}">
            <svg class="h-3 w-3" stroke="currentColor" fill="none" viewBox="0 0 8 8"><path stroke-linecap="round" stroke-width="1.5" d="M1 1l6 6m0-6L1 7" /></svg>
         </button>` : '';

    return `
        <span class="tag-chip ${baseClasses} ${stateClasses} ${interactiveClass}"
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

function renderTagChips(tags, container, isInteractive = true) {
    if (!container) return;
    container.innerHTML = '';
    if (!tags || tags.length === 0) {
        if (container === recentTagsContainer) {
            container.innerHTML = `<p class="text-sm text-gray-500 dark:text-gray-400 italic w-full">No recent tags to show.</p>`;
        } else if (container === tagSearchResultsContainer) {
            container.innerHTML = `<p class="text-xs text-center text-gray-400 dark:text-gray-500 p-2 italic">No tags match your search.</p>`;
        }
        return;
    }
    const fragment = document.createDocumentFragment();
    tags.forEach(tag => {
        const isSelected = selectedTagIds.has(tag.id.toString());
        const chipHtml = createTagChipHtml(tag, isSelected, isInteractive, false);
        const chipElement = document.createElement('div'); 
        chipElement.innerHTML = chipHtml.trim();
        fragment.appendChild(chipElement.firstChild);
    });
    container.appendChild(fragment);
}

function updateSelectedTagsDisplay() {
    if (!selectedTagsDisplay || !noTagsSelectedText || !clearAllTagsButton || !selectedTagsRow) {
        console.warn("[user-tags.js] Missing elements for updating selected tags display.");
        return;
    }
    selectedTagsDisplay.innerHTML = '';

    // --- CONSISTENT ALIGNMENT ---
    // Always use items-start for the row containing the label and the display area.
    selectedTagsRow.classList.remove('items-center'); 
    selectedTagsRow.classList.add('items-start'); 

    if (selectedTagIds.size === 0) {
        selectedTagsDisplay.appendChild(noTagsSelectedText);
        noTagsSelectedText.classList.remove('hidden');
        clearAllTagsButton.classList.add('hidden');
    } else {
        noTagsSelectedText.classList.add('hidden');
        const fragment = document.createDocumentFragment();
        selectedTagIds.forEach(tagId => {
            const tag = allUserTags.find(t => t.id.toString() === tagId);
            if (tag) {
                const chipHtml = createTagChipHtml(tag, true, false, true); // showRemoveIcon is true
                const chipElement = document.createElement('div');
                chipElement.innerHTML = chipHtml.trim();
                fragment.appendChild(chipElement.firstChild);
            }
        });
        selectedTagsDisplay.appendChild(fragment);
        clearAllTagsButton.classList.remove('hidden');
    }
}

function toggleTagSelection(tagId) {
    const tagIdStr = tagId.toString();
    if (selectedTagIds.has(tagIdStr)) {
        selectedTagIds.delete(tagIdStr);
    } else {
        selectedTagIds.add(tagIdStr);
    }
    updateTagChipAppearance(tagIdStr);
    updateSelectedTagsDisplay();
    fetchAndDisplayAssociatedItems();
}

function updateTagChipAppearance(targetTagId) {
    const allInteractiveChips = document.querySelectorAll(
        `#recent-tags-container .tag-chip, #tag-search-results .tag-chip`
    );
    allInteractiveChips.forEach(chip => {
        const currentChipTagId = chip.dataset.tagId.toString();
        // Only update if it's the targetTagId OR if targetTagId is null (meaning reset all)
        if (targetTagId === null || currentChipTagId === targetTagId) {
            const isSelected = selectedTagIds.has(currentChipTagId);

            chip.setAttribute('aria-pressed', isSelected);
            chip.classList.toggle('bg-violet-600', isSelected);
            chip.classList.toggle('text-white', isSelected);
            chip.classList.toggle('hover:bg-violet-700', isSelected);
            chip.classList.toggle('dark:bg-violet-500', isSelected);
            chip.classList.toggle('dark:hover:bg-violet-400', isSelected);

            chip.classList.toggle('bg-violet-100', !isSelected);
            chip.classList.toggle('text-violet-700', !isSelected);
            chip.classList.toggle('hover:bg-violet-200', !isSelected);
            chip.classList.toggle('dark:bg-slate-700', !isSelected);
            chip.classList.toggle('dark:text-violet-300', !isSelected);
            chip.classList.toggle('dark:hover:bg-slate-600', !isSelected);
        }
    });
}

// --- Event Handlers ---
function handleTagChipClick(event) {
    const chip = event.target.closest('.tag-chip');
    if (chip && chip.dataset.tagId) {
        event.preventDefault();
        event.stopPropagation();
        toggleTagSelection(chip.dataset.tagId);
    }
}

function handleRemoveSelectedTagClick(event) {
   const removeButton = event.target.closest('.tag-remove-from-selected');
   if (removeButton && removeButton.dataset.tagId) {
       event.preventDefault();
       event.stopPropagation();
       const tagIdToRemove = removeButton.dataset.tagId.toString();
       if (selectedTagIds.has(tagIdToRemove)) {
           selectedTagIds.delete(tagIdToRemove);
           updateTagChipAppearance(tagIdToRemove); // Update appearance of this specific tag in other lists
           updateSelectedTagsDisplay(); // Re-render the selected tags area
           fetchAndDisplayAssociatedItems(); // Fetch new data based on updated selection
       }
   }
}

function handleTagSearchInput(event) {
    const searchTerm = event.target.value.toLowerCase().trim();
    if (!tagSearchResultsContainer) return;

    if (!searchTerm) {
        tagSearchResultsContainer.innerHTML = searchResultsPlaceholderHtml;
        return;
    }

    const filteredTags = allUserTags.filter(tag =>
        tag.name.toLowerCase().includes(searchTerm)
    );
    renderTagChips(filteredTags, tagSearchResultsContainer, true);
}

function clearAllTagSelections() {
    const previouslySelectedIds = Array.from(selectedTagIds);
    selectedTagIds.clear();
    previouslySelectedIds.forEach(id => updateTagChipAppearance(id));
    updateSelectedTagsDisplay();
    fetchAndDisplayAssociatedItems();
    if(tagSearchInput) tagSearchInput.value = '';
    if(tagSearchResultsContainer) tagSearchResultsContainer.innerHTML = searchResultsPlaceholderHtml;
}

// --- Initialization ---
async function fetchAllUserTags() {
    try {
        const response = await authFetch('/api/tags');
        if (!response.ok) throw new Error(`Failed to fetch tags: ${response.status}`);
        allUserTags = await response.json();
        allUserTags.sort((a, b) => a.name.localeCompare(b.name));
        return allUserTags;
    } catch (error) {
        console.error("Error fetching user tags:", error);
        if (recentTagsContainer) recentTagsContainer.innerHTML = '<p class="text-sm text-red-500 dark:text-red-400 italic w-full">Could not load tags.</p>';
        return [];
    }
}

function setupDeckCardTagListeners() {
     if (decksContainer) {
        decksContainer.removeEventListener('click', handleDeckCardInteraction);
        decksContainer.addEventListener('click', handleDeckCardInteraction);
    }
}
async function handleDeckCardInteraction(event) {
    const removeBtn = event.target.closest('.remove-tag-button');
    const addBtn = event.target.closest('.add-deck-tag-button');

    if (removeBtn && typeof handleRemoveDeckTagClick === 'function') {
        const success = await handleRemoveDeckTagClick(event);
        if (success) fetchAndDisplayAssociatedItems();
    }
    else if (addBtn) {
        event.preventDefault();
        event.stopPropagation();
        const deckId = addBtn.dataset.deckId;
        if (deckId && typeof openQuickAddTagModal === 'function') {
            openQuickAddTagModal(deckId, 'deck', fetchAndDisplayAssociatedItems);
        }
    }
}

function setupMatchCardTagListeners() {
    if (matchesContainer) {
        matchesContainer.removeEventListener('click', handleMatchCardInteraction);
        matchesContainer.addEventListener('click', handleMatchCardInteraction);
    }
}
async function handleMatchCardInteraction(event) {
    const removeBtn = event.target.closest('.remove-match-tag-button');
    const addBtn = event.target.closest('.add-match-tag-button');

    if (removeBtn && typeof handleRemoveMatchTagClick === 'function') {
        const success = await handleRemoveMatchTagClick(event);
        if (success) fetchAndDisplayAssociatedItems();
    }
    else if (addBtn) {
        event.preventDefault();
        event.stopPropagation();
        const matchId = addBtn.dataset.matchId;
        if (matchId && typeof openQuickAddTagModal === 'function') {
            openQuickAddTagModal(matchId, 'match', fetchAndDisplayAssociatedItems);
        }
    }
}

document.addEventListener("DOMContentLoaded", async () => {
    // Guard clause to ensure this script only runs its main logic on the My Tags page
    if (!document.getElementById('tag-selection-area')) {
        return; 
    }

    // Ensure all critical DOM elements for this page are present before proceeding
    if (!recentTagsContainer || !tagSearchInput || !tagSearchResultsContainer || 
        !selectedTagsDisplay || !clearAllTagsButton || !noTagsSelectedText || !selectedTagsRow ||
        !decksContainer || !matchesContainer) {
        console.error("[user-tags.js] Error: One or more essential UI elements for 'My Tags' page not found. Initialization aborted.");
        return;
    }

    await fetchAllUserTags();

    const recentTagsToShow = allUserTags.slice(0, 7);
    renderTagChips(recentTagsToShow, recentTagsContainer, true);
    
    tagSearchInput.addEventListener('input', handleTagSearchInput);
    tagSearchResultsContainer.innerHTML = searchResultsPlaceholderHtml;

    recentTagsContainer.addEventListener('click', handleTagChipClick);
    tagSearchResultsContainer.addEventListener('click', handleTagChipClick);
    selectedTagsDisplay.addEventListener('click', handleRemoveSelectedTagClick);
    clearAllTagsButton.addEventListener('click', clearAllTagSelections);

    setupDeckCardTagListeners();
    setupMatchCardTagListeners();

    if (quickAddModal && quickAddModalCloseBtn && quickAddModalDoneBtn && typeof closeQuickAddTagModal === 'function') {
        quickAddModalCloseBtn.addEventListener('click', closeQuickAddTagModal);
        quickAddModalDoneBtn.addEventListener('click', closeQuickAddTagModal);
        quickAddModal.addEventListener('click', (event) => {
            if (event.target === quickAddModal) {
                closeQuickAddTagModal();
            }
        });
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape' && quickAddModal && !quickAddModal.classList.contains('hidden')) {
                closeQuickAddTagModal();
            }
        });
    } else {
        console.warn("[user-tags.js] Quick Add Tag Modal elements or functions not fully available for My Tags page.");
    }

    updateSelectedTagsDisplay();
    fetchAndDisplayAssociatedItems(); // Initial call to show placeholders or items if tags are pre-selected (e.g. from URL params in future)
});