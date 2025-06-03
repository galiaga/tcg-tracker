// backend/static/js/ui/matches/log-match-modal.js
import { TagInputManager } from '../tagInput.js';
// fetchUserTags is now handled internally by TagInputManager or via its fetchSuggestions option

// --- DOM Elements ---
let modalElement = null;
let modalContentElement = null;
let closeButtonElement = null;
let formElement = null;
let deckSelectElement = null;

// --- State ---
let preselectedInfo = null;
let matchTagInputInstance = null;

// --- Form Management ---
function resetLogMatchForm() {
    if (formElement) {
        formElement.reset();
    }
    if (matchTagInputInstance) {
        matchTagInputInstance.clearTags();
    }
    if (deckSelectElement && deckSelectElement.options.length > 0) {
        deckSelectElement.value = "";
        deckSelectElement.disabled = false;
    }
    const defaultResultRadio = formElement?.querySelector('input[name="match_result"][value="0"]');
    if (defaultResultRadio) {
        defaultResultRadio.checked = true;
    }
    preselectedInfo = null;
}

function applyPreselection() {
    if (preselectedInfo && deckSelectElement) {
        if (preselectedInfo.id) {
            const deckIdToSelect = String(preselectedInfo.id);
            const optionExists = deckSelectElement.querySelector(`option[value="${deckIdToSelect}"]`);
            if (optionExists) {
                deckSelectElement.value = deckIdToSelect;
            } else {
                console.warn(`[log-match-modal] Option for preselected deck ${deckIdToSelect} not found.`);
            }
        } else {
            deckSelectElement.disabled = false;
        }
        if (preselectedInfo.result !== undefined && preselectedInfo.result !== null) {
            const resultRadio = formElement?.querySelector(`input[name="match_result"][value="${preselectedInfo.result}"]`);
            if (resultRadio) {
                resultRadio.checked = true;
            } else {
                console.warn(`[log-match-modal] Radio button for preselected result ${preselectedInfo.result} not found.`);
            }
        }
    } else if (deckSelectElement) {
        deckSelectElement.disabled = false;
    }
}

// --- Modal Visibility & Initialization ---
export function openLogMatchModal(preselectionData = null) {
    if (!modalElement || !modalContentElement) {
        console.error("Cannot open Log Match Modal: Modal DOM elements not initialized.");
        return;
    }
    resetLogMatchForm();
    preselectedInfo = preselectionData;

    if (typeof TagInputManager !== 'undefined' && typeof TagInputManager.init === 'function') {
        if (matchTagInputInstance && typeof matchTagInputInstance.destroy === 'function') {
            matchTagInputInstance.destroy();
        }
        matchTagInputInstance = TagInputManager.init({
            inputId: 'match-tags-input-field',      // ID of the actual <input type="text">
            suggestionsId: 'match-tags-suggestions',  // ID of the suggestions dropdown div
            wrapperId: 'match-tags-input-wrapper',  // ID of the main div styled like an input
            tagsContainerId: 'match-tags-container',// ID of the span where pills are rendered
            // fetchSuggestions can be omitted to use the default internal one in TagInputManager
        });
        if (matchTagInputInstance) {
            const tagInputElement = document.getElementById('match-tags-input-field');
            const firstPositionLabel = document.getElementById('log-match-pos-1');
            if (tagInputElement) {
                 setTimeout(() => {
                    if (preselectedInfo && preselectedInfo.id && preselectedInfo.result !== undefined) {
                        firstPositionLabel?.focus();
                    } else if (preselectedInfo && preselectedInfo.id) {
                         const firstResultRadioLabel = formElement?.querySelector('label[for="log-match-result-win"]');
                         firstResultRadioLabel?.focus();
                    } else {
                        deckSelectElement?.focus();
                    }
                 }, 160);
            }
        } else {
            console.error("[log-match-modal] Failed to initialize TagInputManager instance.");
        }
    } else {
        console.error("[log-match-modal] TagInputManager class or init method not found.");
    }
    applyPreselection();
    modalElement.classList.remove("hidden");
    setTimeout(() => {
        modalContentElement?.classList.remove("scale-95", "opacity-0");
        modalContentElement?.classList.add("scale-100", "opacity-100");
    }, 10);
}

export function closeLogMatchModal() {
    if (!modalElement || !modalContentElement) {
        console.error("Cannot close Log Match Modal: Modal DOM elements not initialized.");
        return;
    }
    if (matchTagInputInstance && typeof matchTagInputInstance.destroy === 'function') {
        matchTagInputInstance.destroy();
    }
    matchTagInputInstance = null;
    preselectedInfo = null;
    modalContentElement.classList.remove("scale-100", "opacity-100");
    modalContentElement.classList.add("scale-95", "opacity-0");
    setTimeout(() => {
        modalElement.classList.add("hidden");
    }, 150);
}

export function getMatchTagInputInstance() {
    return matchTagInputInstance;
}

// --- Event Listener Setup Function ---
function initializeModal() {
    modalElement = document.getElementById("logMatchModal");
    if (!modalElement) {
        console.error("[log-match-modal] Main modal element #logMatchModal not found.");
        return;
    }
    modalContentElement = modalElement.querySelector(".bg-white, .dark\\:bg-gray-800");
    closeButtonElement = document.getElementById("logMatchModalCloseButton");
    formElement = document.getElementById('log-match-form');
    deckSelectElement = document.getElementById("deck-select");

    if (!modalContentElement) console.error("[log-match-modal] Modal content element not found.");
    if (!closeButtonElement) console.error("[log-match-modal] Close button #logMatchModalCloseButton not found.");
    if (!formElement) console.error("[log-match-modal] Form #log-match-form not found.");
    if (!deckSelectElement) console.error("[log-match-modal] Deck select #deck-select not found.");

    if (closeButtonElement) {
        closeButtonElement.addEventListener("click", () => closeLogMatchModal());
    }
    if (modalElement) { // Check modalElement again before adding listener
        modalElement.addEventListener("click", (event) => {
            if (event.target === modalElement) closeLogMatchModal();
        });
    }
    if (formElement) {
        formElement.addEventListener('matchLoggedSuccess', () => closeLogMatchModal());
    }
}

// --- DOMContentLoaded Listener ---
document.addEventListener('DOMContentLoaded', () => {
    initializeModal();
    document.addEventListener('deckOptionsLoaded', () => {
        if (modalElement && !modalElement.classList.contains("hidden")) {
            applyPreselection();
        }
    });
});