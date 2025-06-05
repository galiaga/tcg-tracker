import { TagInputManager } from '../tagInput.js';
import { authFetch } from '../../auth/auth.js';
import { searchCommanders, getCommanderAttributes } from '../../api/deck-api.js'; 

let modalElement = null;
let modalContentElement = null;
let closeButtonElement = null;
let formElement = null;
let deckSelectElement = null;
let podNotesElement = null;
let playerPositionButtonsContainer = null;
let opponentCommandersDynamicContainer = null;
let logMatchTagsPillsContainerElement = null;

let preselectedInfo = null;
let matchTagInputInstance = null;
let selectedTagsForLogMatch = [];
let opponentSlotManagers = {}; 

const VALID_COMMANDER_ROLES = { 
    PRIMARY: "primary",
    PARTNER: "partner",
    BACKGROUND: "background",
    FRIENDS_FOREVER: "friends_forever",
    DOCTOR_COMPANION: "doctor_companion", 
    TIME_LORD_DOCTOR: "time_lord_doctor"    
};

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => { clearTimeout(timeout); func(...args); };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

async function populateDeckSelect() {
    if (!deckSelectElement) return;
    deckSelectElement.disabled = true;
    const originalFirstOptionHTML = deckSelectElement.options.length > 0 && deckSelectElement.options[0].disabled ? deckSelectElement.options[0].outerHTML : '<option disabled selected value="">Select Deck</option>';
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
        deckSelectElement.dispatchEvent(new CustomEvent('deckOptionsLoadedInModal', {bubbles: true}));
    } catch (error) {
        console.error("Failed to fetch decks for log match modal:", error);
        if (deckSelectElement) {
            deckSelectElement.innerHTML = originalFirstOptionHTML;
            const errorOption = document.createElement('option');
            errorOption.disabled = true; errorOption.textContent = "Could not load decks";
            deckSelectElement.appendChild(errorOption);
        }
        if (typeof showFlashMessage === 'function') showFlashMessage(error.message || "Could not load your decks.", "danger");
    }
}

function resetLogMatchForm() {
    if (formElement) formElement.reset(); 
    selectedTagsForLogMatch = [];
    if (logMatchTagsPillsContainerElement) {
        logMatchTagsPillsContainerElement.innerHTML = '';
    }
    matchTagInputInstance?.clearInput?.();
    if (deckSelectElement?.options.length > 0) {
        deckSelectElement.value = ""; 
        deckSelectElement.disabled = false;
    }
    
    const defaultResultRadio = formElement?.querySelector('input[name="match_result"][value="0"]');
    if (defaultResultRadio) { 
        defaultResultRadio.checked = true;
    } else {
        console.warn("Could not find default result radio button (Win) to check in resetLogMatchForm.");
        if (!formElement) {
            console.warn("`formElement` is null or undefined in resetLogMatchForm.");
        }
    }

    formElement?.querySelectorAll('input[name="player_position_radio"]').forEach(radio => radio.checked = false);
    formElement?.querySelectorAll('input[name="player_mulligans_radio"]').forEach(radio => radio.checked = false);
    
    if (opponentCommandersDynamicContainer) opponentCommandersDynamicContainer.innerHTML = '';
    Object.values(opponentSlotManagers).forEach(slot => { 
        slot.primaryInputManager?.destroy?.();
        slot.associatedInputManager?.destroy?.();
    });
    opponentSlotManagers = {};

    if (podNotesElement) podNotesElement.value = '';
    preselectedInfo = null;
}

function applyPreselection() {
    if (!deckSelectElement) return;
    if (preselectedInfo) {
        if (preselectedInfo.id) {
            const deckIdToSelect = String(preselectedInfo.id);
            const optionExists = deckSelectElement.querySelector(`option[value="${deckIdToSelect}"]`);
            if (optionExists) {
                deckSelectElement.value = deckIdToSelect;
                deckSelectElement.disabled = true;
            } else {
                deckSelectElement.disabled = false;
            }
        } else {
            deckSelectElement.disabled = false;
        }
        if (preselectedInfo.result !== undefined && preselectedInfo.result !== null) {
            const resultRadio = formElement?.querySelector(`input[name="match_result"][value="${preselectedInfo.result}"]`);
            if (resultRadio) resultRadio.checked = true;
        }
    } else if (deckSelectElement) {
        deckSelectElement.disabled = false;
    }
}

function renderGenericPill(dataToPill, container, onRemoveCallback) {
    if (!container) {
        console.error("RenderPill: Container not found for pill.");
        return null;
    }
    if (!dataToPill || typeof dataToPill.id === 'undefined' || typeof dataToPill.name === 'undefined') {
        console.error("RenderPill: Invalid dataToPill object. Must have id and name.", dataToPill);
        return null;
    }

    const pill = document.createElement('span');
    pill.className = 'tag-pill inline-flex items-center whitespace-nowrap bg-sky-100 dark:bg-sky-700/60 px-2.5 py-1 text-xs font-semibold text-sky-700 dark:text-sky-200 rounded-full';
    
    try {
        pill.dataset.id = String(dataToPill.id); 
    } catch (e) {
        console.error("Error assigning to pill.dataset.id:", e, "dataToPill.id was:", dataToPill.id);
    }
    
    const nameSpan = document.createElement('span');
    nameSpan.textContent = dataToPill.name;
    pill.appendChild(nameSpan);

    const removeBtn = document.createElement('button');
    removeBtn.type = 'button';
    removeBtn.className = 'ml-1.5 -mr-0.5 flex-shrink-0 rounded-full p-0.5 text-sky-500 dark:text-sky-400 hover:bg-sky-200 dark:hover:bg-sky-600 focus:outline-none focus:ring-1 focus:ring-sky-400 dark:focus:ring-sky-500';
    removeBtn.innerHTML = `<svg class="h-2.5 w-2.5" stroke="currentColor" fill="none" viewBox="0 0 8 8"><path stroke-linecap="round" stroke-width="1.5" d="M1 1l6 6m0-6L1 7" /></svg>`;
    removeBtn.setAttribute('aria-label', `Remove ${dataToPill.name}`);
    removeBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        onRemoveCallback(dataToPill, pill);
    });
    pill.appendChild(removeBtn);
    container.appendChild(pill);
    return pill;
}


function createOpponentCommanderSlot(seatNumber) {
    if (!opponentCommandersDynamicContainer) {
        console.error("`opponentCommandersDynamicContainer` is not defined in `createOpponentCommanderSlot`");
        return;
    }

    const slotWrapper = document.createElement('div');
    slotWrapper.className = 'opponent-commander-slot border-t border-gray-200 dark:border-gray-700 pt-3 space-y-2';
    slotWrapper.dataset.seatNumber = seatNumber;

    const label = document.createElement('label');
    label.className = 'block text-sm font-medium text-gray-700 dark:text-gray-300';
    label.textContent = `Seat ${seatNumber} Commander(s)`;
    slotWrapper.appendChild(label);

    const pillsContainerId = `seat-${seatNumber}-pills-container`;
    const pillsContainer = document.createElement('div');
    pillsContainer.id = pillsContainerId;
    pillsContainer.className = 'pills-container mb-1 flex flex-wrap gap-1.5 min-h-[28px] items-center';
    slotWrapper.appendChild(pillsContainer);

    const primaryInputId = `seat-${seatNumber}-primary-commander-input`;
    const primarySuggestionsId = `seat-${seatNumber}-primary-suggestions`;
    const primaryInputArea = document.createElement('div');
    primaryInputArea.className = 'relative input-area primary-input-area';
    primaryInputArea.innerHTML = `
        <input type="text" id="${primaryInputId}" placeholder="Search Primary Commander..." autocomplete="off"
               class="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 shadow-sm focus:border-violet-500 focus:ring-1 focus:ring-violet-500 placeholder-gray-400 dark:placeholder-gray-500">
        <ul id="${primarySuggestionsId}" class="suggestions-list hidden absolute z-30 mt-1 w-full bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-md shadow-lg max-h-48 overflow-y-auto"></ul>
    `;
    slotWrapper.appendChild(primaryInputArea);
    
    const addAssociatedButton = document.createElement('button');
    addAssociatedButton.type = 'button';
    addAssociatedButton.id = `seat-${seatNumber}-add-associated-btn`;
    addAssociatedButton.className = 'add-associated-btn text-xs font-medium text-violet-600 dark:text-violet-400 hover:text-violet-800 dark:hover:text-violet-200 border border-dashed border-violet-400 dark:border-violet-500 rounded-full px-2 py-0.5 mt-1 hidden';
    addAssociatedButton.textContent = '+ Add Partner/Associated';
    slotWrapper.appendChild(addAssociatedButton);

    const associatedInputId = `seat-${seatNumber}-associated-commander-input`;
    const associatedSuggestionsId = `seat-${seatNumber}-associated-suggestions`;
    const associatedInputArea = document.createElement('div');
    associatedInputArea.className = 'relative input-area associated-input-area mt-2 hidden';
    associatedInputArea.innerHTML = `
        <input type="text" id="${associatedInputId}" placeholder="Search Associated Commander..." autocomplete="off"
               class="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 shadow-sm focus:border-violet-500 focus:ring-1 focus:ring-violet-500 placeholder-gray-400 dark:placeholder-gray-500">
        <ul id="${associatedSuggestionsId}" class="suggestions-list hidden absolute z-30 mt-1 w-full bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-md shadow-lg max-h-48 overflow-y-auto"></ul>
    `;
    slotWrapper.appendChild(associatedInputArea);
    
    opponentCommandersDynamicContainer.appendChild(slotWrapper);

    opponentSlotManagers[seatNumber] = { 
        primaryCommander: null, 
        associatedCommander: null, 
        primaryPillElement: null,
        associatedPillElement: null,
        primaryInputManager: null,
        associatedInputManager: null,
        slotWrapper: slotWrapper,
        pairingType: 'unknown' 
    };
    
    const primaryTM = TagInputManager.init({ 
        inputId: primaryInputId,
        suggestionsId: primarySuggestionsId,
        searchFunction: async (query) => {
            return searchCommanders(query); 
        }, 
        renderSuggestionItem: (commander) => {
            return `<li class="px-4 py-2 hover:bg-violet-100 dark:hover:bg-violet-700 cursor-pointer flex items-center text-sm text-gray-700 dark:text-gray-200">${commander.image_url ? `<img src="${commander.image_url}" alt="${commander.name}" class="w-8 h-10 mr-2 object-contain rounded-sm">` : ''} <span class="truncate">${commander.name}</span></li>`;
        },
        onTagAdded: async (commander) => { 
            if (opponentSlotManagers[seatNumber].primaryCommander) return; 

            opponentSlotManagers[seatNumber].primaryCommander = commander;
            opponentSlotManagers[seatNumber].primaryPillElement = renderGenericPill(commander, pillsContainer, () => {
                opponentSlotManagers[seatNumber].primaryCommander = null;
                opponentSlotManagers[seatNumber].primaryPillElement?.remove();
                opponentSlotManagers[seatNumber].primaryPillElement = null;
                primaryInputArea.style.display = 'block'; 
                addAssociatedButton.classList.add('hidden');
                associatedInputArea.classList.add('hidden');
                opponentSlotManagers[seatNumber].associatedInputManager?.clearInput?.();
                opponentSlotManagers[seatNumber].associatedCommander = null;
                opponentSlotManagers[seatNumber].associatedPillElement?.remove();
                opponentSlotManagers[seatNumber].associatedPillElement = null;
                opponentSlotManagers[seatNumber].pairingType = 'unknown'; 
            });
            primaryInputArea.style.display = 'none'; 

            try {
                const attributes = await getCommanderAttributes(commander.id);
                const determinedPairingType = 
                    attributes.partner ? VALID_COMMANDER_ROLES.PARTNER :
                    attributes.friends_forever ? VALID_COMMANDER_ROLES.FRIENDS_FOREVER :
                    attributes.choose_a_background ? VALID_COMMANDER_ROLES.BACKGROUND :
                    attributes.time_lord_doctor ? VALID_COMMANDER_ROLES.DOCTOR_COMPANION : 
                    attributes.doctor_companion ? VALID_COMMANDER_ROLES.TIME_LORD_DOCTOR : 
                    'unknown';
                
                opponentSlotManagers[seatNumber].pairingType = determinedPairingType; 

                if (determinedPairingType !== 'unknown') {
                    addAssociatedButton.classList.remove('hidden');
                } else {
                    addAssociatedButton.classList.add('hidden');
                }
            } catch (e) { 
                console.error(`[Seat ${seatNumber}] Error fetching commander attributes for ${commander.name}:`, e); 
                addAssociatedButton.classList.add('hidden');
                opponentSlotManagers[seatNumber].pairingType = 'unknown';
            }
        },
        isCommanderSearch: true // Indicate this is for commanders
    });
    if (!primaryTM) {
        console.error(`[Seat ${seatNumber}] Failed to initialize Primary TagInputManager!`);
    }
    opponentSlotManagers[seatNumber].primaryInputManager = primaryTM;

    addAssociatedButton.addEventListener('click', () => {
        const currentPairingType = opponentSlotManagers[seatNumber].pairingType; // Get stored pairing type

        associatedInputArea.classList.remove('hidden');
        document.getElementById(associatedInputId)?.focus();
        addAssociatedButton.classList.add('hidden'); 

        if (opponentSlotManagers[seatNumber].associatedInputManager) {
            opponentSlotManagers[seatNumber].associatedInputManager.destroy();
        }
        
        const associatedTM = TagInputManager.init({
            inputId: associatedInputId,
            suggestionsId: associatedSuggestionsId,
            searchFunction: async (query) => {
                return searchCommanders(query, currentPairingType); // Pass the pairingType
            },
            renderSuggestionItem: (commander) => `<li class="px-4 py-2 hover:bg-violet-100 dark:hover:bg-violet-700 cursor-pointer flex items-center text-sm text-gray-700 dark:text-gray-200">${commander.image_url ? `<img src="${commander.image_url}" alt="${commander.name}" class="w-8 h-10 mr-2 object-contain rounded-sm">` : ''} <span class="truncate">${commander.name}</span></li>`,
            onTagAdded: (commander) => {
                if (opponentSlotManagers[seatNumber].associatedCommander) return; 
                if (opponentSlotManagers[seatNumber].primaryCommander?.id === commander.id) {
                     if(typeof showFlashMessage === 'function') showFlashMessage("Associated commander cannot be the same as the primary.", "warning");
                     associatedTM.clearInput(); 
                     return;
                }
                // Client-side validation for pairing type (optional but good UX)
                getCommanderAttributes(commander.id).then(assocAttributes => {
                    let isValidPair = false;
                    const primaryAttrs = opponentSlotManagers[seatNumber].primaryCommander ? getCommanderAttributes(opponentSlotManagers[seatNumber].primaryCommander.id) : Promise.resolve({}); // Fetch primary again or ensure it's stored
                    
                    // This validation logic needs to be robust and match backend
                    // For simplicity, we'll assume currentPairingType is the attribute the *associated* card must have
                    // e.g. if primary is "Partner", associated must have "Partner"
                    // if primary is "Time Lord Doctor", associated must be "Doctor's Companion"
                    if (currentPairingType === VALID_COMMANDER_ROLES.PARTNER && assocAttributes.partner) isValidPair = true;
                    else if (currentPairingType === VALID_COMMANDER_ROLES.FRIENDS_FOREVER && assocAttributes.friends_forever) isValidPair = true;
                    else if (currentPairingType === VALID_COMMANDER_ROLES.BACKGROUND && assocAttributes.background) isValidPair = true; // Primary needs "Choose a Background", this IS a background
                    else if (currentPairingType === VALID_COMMANDER_ROLES.DOCTOR_COMPANION && assocAttributes.doctor_companion) isValidPair = true; // Primary is Doctor, this IS a companion
                    else if (currentPairingType === VALID_COMMANDER_ROLES.TIME_LORD_DOCTOR && assocAttributes.time_lord_doctor) isValidPair = true; // Primary is Companion, this IS a doctor
                    else if (currentPairingType === 'unknown') isValidPair = true; // Should not happen if button was shown

                    if (!isValidPair) {
                        if(typeof showFlashMessage === 'function') showFlashMessage(`'${commander.name}' is not a valid ${currentPairingType} for the selected primary commander.`, "warning");
                        associatedTM.clearInput();
                        return;
                    }

                    opponentSlotManagers[seatNumber].associatedCommander = commander;
                    opponentSlotManagers[seatNumber].associatedPillElement = renderGenericPill(commander, pillsContainer, () => {
                        opponentSlotManagers[seatNumber].associatedCommander = null;
                        opponentSlotManagers[seatNumber].associatedPillElement?.remove();
                        opponentSlotManagers[seatNumber].associatedPillElement = null;
                        associatedInputArea.classList.add('hidden');
                        if (opponentSlotManagers[seatNumber].primaryCommander && opponentSlotManagers[seatNumber].pairingType !== 'unknown') { 
                           addAssociatedButton.classList.remove('hidden'); 
                        }
                    });
                    associatedInputArea.classList.add('hidden'); 
                }).catch(err => {
                    console.error("Error validating associated commander attributes:", err);
                });
            },
            isCommanderSearch: true // Indicate this is for commanders
        });
        if (!associatedTM) {
            console.error(`[Seat ${seatNumber}] Failed to initialize Associated TagInputManager!`);
        }
        opponentSlotManagers[seatNumber].associatedInputManager = associatedTM;
    });
}

function handlePlayerPositionChange() {
    if (!formElement || !opponentCommandersDynamicContainer) return;
    const selectedPositionRadio = formElement.querySelector('input[name="player_position_radio"]:checked');
    
    opponentCommandersDynamicContainer.innerHTML = ''; 
    Object.values(opponentSlotManagers).forEach(slot => {
        slot.primaryInputManager?.destroy?.();
        slot.associatedInputManager?.destroy?.();
    });
    opponentSlotManagers = {};

    if (!selectedPositionRadio) {
        opponentCommandersDynamicContainer.classList.add('hidden');
        return;
    }
    const playerSeat = parseInt(selectedPositionRadio.value);
    
    let opponentSeatCount = 0;
    for (let seat = 1; seat <= 4; seat++) {
        if (seat !== playerSeat) {
            createOpponentCommanderSlot(seat);
            opponentSeatCount++;
        }
    }
    if (opponentSeatCount > 0) {
        opponentCommandersDynamicContainer.classList.remove('hidden');
    } else {
        opponentCommandersDynamicContainer.classList.add('hidden');
    }
}

export async function openLogMatchModal(preselectionData = null) {
    if (!modalElement || !modalContentElement || !formElement) return;
    resetLogMatchForm(); 
    preselectedInfo = preselectionData;
    await populateDeckSelect(); 
    applyPreselection();    

    if (typeof TagInputManager?.init === 'function') {
        if (matchTagInputInstance?.destroy) matchTagInputInstance.destroy();
        matchTagInputInstance = TagInputManager.init({
            inputId: 'match-tags-input-field',
            suggestionsId: 'match-tags-suggestions',
            onTagAdded: (tagData) => {
                if (!selectedTagsForLogMatch.some(t => t.id === tagData.id)) {
                    selectedTagsForLogMatch.push(tagData);
                    renderGenericPill(tagData, logMatchTagsPillsContainerElement, 
                        (removedTag, pillElement) => {
                            selectedTagsForLogMatch = selectedTagsForLogMatch.filter(t => t.id !== removedTag.id);
                            pillElement.remove();
                        }
                    );
                }
            },
            isCommanderSearch: false 
        });
        setTimeout(() => {
            const firstDeckOption = deckSelectElement?.querySelector('option:not([disabled])');
            if (deckSelectElement && !deckSelectElement.disabled && deckSelectElement.value === "" && firstDeckOption) {
                deckSelectElement.focus();
            } else {
                document.getElementById('log-match-pos-1')?.focus();
            }
        }, 160);
    }
    handlePlayerPositionChange(); 

    modalElement.classList.remove("hidden");
    setTimeout(() => {
        modalContentElement?.classList.remove("scale-95", "opacity-0");
        modalContentElement?.classList.add("scale-100", "opacity-100");
    }, 10);
}

export function closeLogMatchModal() {
    if (!modalElement || !modalContentElement) return;
    if (matchTagInputInstance?.destroy) matchTagInputInstance.destroy();
    matchTagInputInstance = null;
    
    Object.values(opponentSlotManagers).forEach(slot => {
        slot.primaryInputManager?.destroy?.();
        slot.associatedInputManager?.destroy?.();
    });
    opponentSlotManagers = {};

    preselectedInfo = null;
    selectedTagsForLogMatch = [];
    modalContentElement.classList.remove("scale-100", "opacity-100");
    modalContentElement.classList.add("scale-95", "opacity-0");
    setTimeout(() => modalElement.classList.add("hidden"), 150);
}

export function getSelectedTagIdsForCurrentMatch() {
    return selectedTagsForLogMatch.map(tag => tag.id);
}

export function getOpponentCommandersData() {
    const dataBySeat = {};
    Object.keys(opponentSlotManagers).forEach(seatNumberStr => {
        const seatNumber = parseInt(seatNumberStr);
        const slot = opponentSlotManagers[seatNumber];
        const commandersForSeat = [];
        if (slot.primaryCommander) {
            commandersForSeat.push({ id: slot.primaryCommander.id, role: VALID_COMMANDER_ROLES.PRIMARY });
        }
        if (slot.associatedCommander) {
            const pairingType = slot.pairingType || VALID_COMMANDER_ROLES.PARTNER; 
            commandersForSeat.push({ id: slot.associatedCommander.id, role: pairingType });
        }
        if (commandersForSeat.length > 0) {
            dataBySeat[seatNumber] = commandersForSeat;
        }
    });
    return dataBySeat;
}

function initializeModal() {
    modalElement = document.getElementById("logMatchModal");
    if (!modalElement) return;
    modalContentElement = modalElement.querySelector(".bg-white, .dark\\:bg-gray-800");
    closeButtonElement = document.getElementById("logMatchModalCloseButton");
    formElement = document.getElementById('log-match-form');
    deckSelectElement = document.getElementById("deck-select"); 
    podNotesElement = document.getElementById('log-match-pod-notes');
    playerPositionButtonsContainer = document.getElementById('player-position-buttons');
    opponentCommandersDynamicContainer = document.getElementById('opponent-commanders-dynamic-container');
    logMatchTagsPillsContainerElement = document.getElementById('log-match-tags-pills-container');

    if (!formElement || !playerPositionButtonsContainer || !opponentCommandersDynamicContainer || !logMatchTagsPillsContainerElement) { 
        console.error("[log-match-modal.js] Critical dynamic content container(s) not found in modal.");
        return; 
    };

    playerPositionButtonsContainer.addEventListener('change', handlePlayerPositionChange);
    
    document.addEventListener("click", function(event) { 
        document.querySelectorAll('.suggestions-list').forEach(list => {
            const parentInputArea = list.closest('.input-area');
            if (parentInputArea && !parentInputArea.contains(event.target)) {
                list.style.display = "none";
            }
        });
    });
    
    if (closeButtonElement) closeButtonElement.addEventListener("click", closeLogMatchModal);
    modalElement.addEventListener("click", (event) => {
        if (event.target === modalElement) closeLogMatchModal();
    });
    formElement.addEventListener('matchLoggedSuccess', closeLogMatchModal); 
}

document.addEventListener('DOMContentLoaded', () => {
    initializeModal();
});