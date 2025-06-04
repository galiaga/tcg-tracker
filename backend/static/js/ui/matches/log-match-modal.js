// backend/static/js/ui/matches/log-match-modal.js

import { TagInputManager } from '../tagInput.js';
import { authFetch } from '../../auth/auth.js'; // Needed for populateDeckSelect

// --- DOM Elements ---
let modalElement = null;
let modalContentElement = null;
let closeButtonElement = null;
let formElement = null;
let deckSelectElement = null; // This will be document.getElementById('deck-select')

// --- State ---
let preselectedInfo = null;
let matchTagInputInstance = null;
let selectedTagsForLogMatch = [];

// --- Deck Population (MOVED HERE) ---
async function populateDeckSelect() {
    // deckSelectElement is already defined at the module scope and initialized in initializeModal
    if (!deckSelectElement) {
        console.warn("[log-match-modal.js -> populateDeckSelect] Deck select element not found in modal.");
        return;
    }
    deckSelectElement.disabled = true;
    const originalFirstOptionHTML = deckSelectElement.options.length > 0 && deckSelectElement.options[0].disabled ?
                                   deckSelectElement.options[0].outerHTML :
                                   '<option disabled selected value="">Select Deck</option>';
    deckSelectElement.innerHTML = '<option disabled selected value="">Loading decks...</option>';
    try {
        const response = await authFetch("/api/user_decks");
        if (!response || !response.ok) {
             const errorData = response ? await response.json().catch(() => ({})) : {};
             throw new Error(errorData.error || `Failed to fetch decks (${response?.status})`);
         }
        const decks = await response.json();
        
        deckSelectElement.innerHTML = originalFirstOptionHTML;

        if (Array.isArray(decks) && decks.length > 0) {
            decks.forEach(deck => {
                const option = document.createElement("option");
                option.value = deck.id;
                option.dataset.name = deck.name;
                option.textContent = deck.name;
                deckSelectElement.appendChild(option);
            });
             deckSelectElement.disabled = false;
        } else {
             if (!deckSelectElement.querySelector('option[value=""]')) {
                deckSelectElement.innerHTML = '<option disabled selected value="">No decks available</option>';
             }
        }
        // Dispatch event on the modal's form or deckSelect itself if needed by other parts of this modal
        deckSelectElement.dispatchEvent(new CustomEvent('deckOptionsLoadedInModal', {bubbles: true}));
    } catch (error) {
        console.error("Failed to fetch decks for log match modal:", error);
        if (deckSelectElement) {
            deckSelectElement.innerHTML = originalFirstOptionHTML;
            const errorOption = document.createElement('option');
            errorOption.disabled = true;
            errorOption.textContent = "Could not load decks";
            deckSelectElement.appendChild(errorOption);
        }
         if (typeof showFlashMessage === 'function') {
             showFlashMessage(error.message || "Could not load your decks.", "danger");
         }
    }
}


// --- Form Management ---
function resetLogMatchForm() {
    if (formElement) {
        formElement.reset(); // This should uncheck radios that don't have 'checked' in HTML
    }
    selectedTagsForLogMatch = [];
    const logMatchPillsContainer = document.getElementById('log-match-tags-pills-container');
    if (logMatchPillsContainer) {
        logMatchPillsContainer.innerHTML = '';
    }
    if (matchTagInputInstance && typeof matchTagInputInstance.clearInput === 'function') {
        matchTagInputInstance.clearInput();
    }
    if (deckSelectElement && deckSelectElement.options.length > 0) {
        deckSelectElement.value = ""; // Reset to placeholder
        deckSelectElement.disabled = false;
    }
    
    // Ensure result defaults to Win (or your preferred default)
    const defaultResultRadio = formElement?.querySelector('input[name="match_result"][value="0"]');
    if (defaultResultRadio) {
        defaultResultRadio.checked = true;
    }

    // --- Explicitly uncheck player position ---
    // This might be redundant if form.reset() works as expected after HTML change,
    // but it's a safeguard.
    const playerPositionRadios = formElement?.querySelectorAll('input[name="player_position_radio"]');
    if (playerPositionRadios) {
        playerPositionRadios.forEach(radio => radio.checked = false);
    }
    // --- End of explicit uncheck ---

    preselectedInfo = null;
}

function applyPreselection() {
    if (!deckSelectElement) {
        console.warn("[log-match-modal] Deck select element not available for applyPreselection.");
        return;
    }
    if (preselectedInfo) {
        if (preselectedInfo.id) {
            const deckIdToSelect = String(preselectedInfo.id);
            const optionExists = deckSelectElement.querySelector(`option[value="${deckIdToSelect}"]`);
            if (optionExists) {
                deckSelectElement.value = deckIdToSelect;
                deckSelectElement.disabled = true;
            } else {
                console.warn(`[log-match-modal] Option for preselected deck ${deckIdToSelect} not found AFTER populating.`);
                deckSelectElement.disabled = false;
            }
        } else {
            deckSelectElement.disabled = false;
        }
        if (preselectedInfo.result !== undefined && preselectedInfo.result !== null) {
            const resultRadio = formElement?.querySelector(`input[name="match_result"][value="${preselectedInfo.result}"]`);
            if (resultRadio) resultRadio.checked = true;
            else console.warn(`[log-match-modal] Radio for preselected result ${preselectedInfo.result} not found.`);
        }
    } else if (deckSelectElement) {
        deckSelectElement.disabled = false;
    }
}

function renderLogMatchTagPill(tagData) {
    const container = document.getElementById('log-match-tags-pills-container');
    if (!container) return;
    const pill = document.createElement('span');
    pill.className = 'tag-pill inline-flex items-center whitespace-nowrap bg-violet-100 dark:bg-violet-700/60 px-2.5 py-1 text-xs font-semibold text-violet-700 dark:text-violet-200 rounded-full';
    pill.dataset.tagId = tagData.id;
    const tagNameSpan = document.createElement('span');
    tagNameSpan.textContent = tagData.name;
    pill.appendChild(tagNameSpan);
    const removeBtn = document.createElement('button');
    removeBtn.type = 'button';
    removeBtn.className = 'ml-1.5 -mr-0.5 flex-shrink-0 rounded-full p-0.5 text-violet-500 dark:text-violet-400 hover:bg-violet-200 dark:hover:bg-violet-600 focus:outline-none focus:ring-1 focus:ring-violet-400 dark:focus:ring-violet-500';
    removeBtn.innerHTML = `<svg class="h-2.5 w-2.5" stroke="currentColor" fill="none" viewBox="0 0 8 8"><path stroke-linecap="round" stroke-width="1.5" d="M1 1l6 6m0-6L1 7" /></svg>`;
    removeBtn.setAttribute('aria-label', `Remove ${tagData.name}`);
    removeBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        selectedTagsForLogMatch = selectedTagsForLogMatch.filter(t => t.id !== tagData.id);
        pill.remove();
        const inputField = document.getElementById('match-tags-input-field');
        if (inputField) inputField.focus();
    });
    pill.appendChild(removeBtn);
    container.appendChild(pill);
}

// --- Modal Visibility & Initialization ---
export async function openLogMatchModal(preselectionData = null) {
    if (!modalElement || !modalContentElement || !formElement) { // Ensure formElement is also checked
        console.error("Cannot open Log Match Modal: Essential Modal DOM elements not initialized (modal, content, or form).");
        return;
    }
    resetLogMatchForm();
    preselectedInfo = preselectionData;

    await populateDeckSelect(); // Call local populateDeckSelect and wait
    applyPreselection();    // Apply preselection after decks are loaded

    if (typeof TagInputManager !== 'undefined' && typeof TagInputManager.init === 'function') {
        if (matchTagInputInstance && typeof matchTagInputInstance.destroy === 'function') {
            matchTagInputInstance.destroy();
        }
        matchTagInputInstance = TagInputManager.init({
            inputId: 'match-tags-input-field',
            suggestionsId: 'match-tags-suggestions',
            onTagAdded: (tagData) => {
                if (!selectedTagsForLogMatch.some(t => t.id === tagData.id)) {
                    selectedTagsForLogMatch.push(tagData);
                    renderLogMatchTagPill(tagData);
                }
            }
        });
        if (matchTagInputInstance && typeof matchTagInputInstance.clearInput === 'function') {
            // Focus logic (can be simplified or adjusted)
            setTimeout(() => {
                const firstPositionLabel = document.getElementById('log-match-pos-1');
                if (preselectedInfo && preselectedInfo.id && preselectedInfo.result !== undefined) {
                    firstPositionLabel?.focus();
                } else if (preselectedInfo && preselectedInfo.id) {
                    formElement?.querySelector('label[for="log-match-result-win"]')?.focus();
                } else if (deckSelectElement && !deckSelectElement.disabled) {
                    deckSelectElement.focus();
                } else {
                    firstPositionLabel?.focus();
                }
            }, 160);
        } else if (!matchTagInputInstance) {
            console.error("[log-match-modal] Failed to initialize TagInputManager instance.");
        }
    } else {
        console.error("[log-match-modal] TagInputManager class or init method not found.");
    }

    modalElement.classList.remove("hidden");
    setTimeout(() => {
        modalContentElement?.classList.remove("scale-95", "opacity-0");
        modalContentElement?.classList.add("scale-100", "opacity-100");
    }, 10);
}

export function closeLogMatchModal() {
    if (!modalElement || !modalContentElement) return;
    if (matchTagInputInstance && typeof matchTagInputInstance.destroy === 'function') {
        matchTagInputInstance.destroy();
    }
    matchTagInputInstance = null;
    preselectedInfo = null;
    selectedTagsForLogMatch = [];
    modalContentElement.classList.remove("scale-100", "opacity-100");
    modalContentElement.classList.add("scale-95", "opacity-0");
    setTimeout(() => {
        modalElement.classList.add("hidden");
    }, 150);
}

export function getSelectedTagIdsForCurrentMatch() {
    return selectedTagsForLogMatch.map(tag => tag.id);
}

// --- Event Listener Setup Function ---
function initializeModal() {
    modalElement = document.getElementById("logMatchModal");
    if (!modalElement) return;

    modalContentElement = modalElement.querySelector(".bg-white, .dark\\:bg-gray-800");
    closeButtonElement = document.getElementById("logMatchModalCloseButton");
    formElement = document.getElementById('log-match-form');
    deckSelectElement = document.getElementById("deck-select"); // Initialize here

    if (!formElement) {
        console.error("[log-match-modal] Form #log-match-form not found inside #logMatchModal. Submission will not work.");
        return; // Critical if form is missing
    }
    
    // The submit listener should be in log-match.js as it contains handleLogMatchSubmit
    // This modal script should only manage its own UI and state.
    // We can import handleLogMatchSubmit here if we want to keep all modal logic together.
    // For now, assuming log-match.js adds the submit listener to this formElement.

    if (closeButtonElement) {
        closeButtonElement.addEventListener("click", closeLogMatchModal);
    }
    modalElement.addEventListener("click", (event) => {
        if (event.target === modalElement) closeLogMatchModal();
    });
    formElement.addEventListener('matchLoggedSuccess', closeLogMatchModal); // Listen to event from handleLogMatchSubmit
}

document.addEventListener('DOMContentLoaded', () => {
    initializeModal();
    // No longer need to listen for 'deckOptionsLoaded' here as openLogMatchModal handles population
});