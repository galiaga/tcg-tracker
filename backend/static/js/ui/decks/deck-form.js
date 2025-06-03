// backend/static/js/ui/decks/deck-form.js
import { searchCommanders, getCommanderAttributes } from '../../api/deck-api.js';

// --- Configuration ---
const FIELD_CONFIG = {
    commander: { inputId: "commander_name", suggestionsId: "commander-suggestions", fieldId: "commanderField", datasetKey: "commanderId" },
    partner: { inputId: "partner_name", suggestionsId: "partner-suggestions", fieldId: "partnerField", datasetKey: "partnerId" },
    friendsForever: { inputId: "friendsForever_name", suggestionsId: "friendsForever-suggestions", fieldId: "friendsForeverField", datasetKey: "friendsForeverId" },
    doctorCompanion: { inputId: "doctorCompanion_name", suggestionsId: "doctorCompanion-suggestions", fieldId: "doctorCompanionField", datasetKey: "doctorCompanionId" }, // CORRECTED
    timeLordDoctor: { inputId: "timeLordDoctor_name", suggestionsId: "timeLordDoctor-suggestions", fieldId: "timeLordDoctorField", datasetKey: "timeLordDoctorId" },   // CORRECTED
    chooseABackground: { inputId: "chooseABackground_name", suggestionsId: "chooseABackground-suggestions", fieldId: "chooseABackgroundField", datasetKey: "backgroundId" }
};

const conditionalFieldPrefixes = Object.keys(FIELD_CONFIG);

// --- Utility Functions ---
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// --- DOMContentLoaded ---
document.addEventListener("DOMContentLoaded", function () {

    const commanderField = document.getElementById(FIELD_CONFIG.commander.fieldId);
    const commanderInput = document.getElementById(FIELD_CONFIG.commander.inputId);

    let selectedCommanderId = null;

    if (!commanderField || !commanderInput) {
        console.error("[deck-form.js] CRITICAL: Commander field or input element not found. Cannot initialize commander logic.");
        return;
    }

    commanderField.style.display = "block";
    hideAllAssociatedFields();

    // --- Dynamic Field Visibility Logic ---
    function hideAllAssociatedFields() {
        conditionalFieldPrefixes.forEach(type => {
            if (type !== 'commander') {
                const config = FIELD_CONFIG[type];
                const fieldElement = document.getElementById(config.fieldId);
                const inputElement = document.getElementById(config.inputId);
                if (fieldElement) {
                    fieldElement.style.display = "none";
                }
                 if (inputElement) {
                     inputElement.value = '';
                     // Use config.datasetKey directly (it's already camelCase)
                     delete inputElement.dataset[config.datasetKey];
                }
            }
        });
    }

    async function checkCommanderRelations(commanderId) {
        hideAllAssociatedFields();
        if (!commanderId) {
            selectedCommanderId = null;
            return;
        }
        try {
            const commanderData = await getCommanderAttributes(commanderId);
            selectedCommanderId = commanderData.id;

            if (commanderData.partner) showAssociatedField('partner');
            if (commanderData.friends_forever) showAssociatedField('friendsForever');
            if (commanderData.doctor_companion) showAssociatedField('timeLordDoctor'); // This refers to the ability of the main commander
            if (commanderData.time_lord_doctor) showAssociatedField('doctorCompanion'); // This refers to the ability of the main commander
            if (commanderData.choose_a_background) showAssociatedField('chooseABackground');

        } catch (error) {
            console.error("Error checking commander relations:", error.message);
            selectedCommanderId = null;
        }
    }

    function showAssociatedField(type) {
        const config = FIELD_CONFIG[type];
        if (!config) return;
        const fieldElement = document.getElementById(config.fieldId);
        if (fieldElement) {
            fieldElement.style.display = "block";
        }
    }

    // --- Autocomplete Suggestion Logic ---
    function handleSuggestionClick(type, commander, suggestionsListElement) {
        const config = FIELD_CONFIG[type];
        if (!config) return;

        const inputElement = document.getElementById(config.inputId);
        inputElement.value = commander.name;
        // Use the camelCase key directly from FIELD_CONFIG
        inputElement.dataset[config.datasetKey] = commander.id; 

        suggestionsListElement.innerHTML = '';
        suggestionsListElement.style.display = 'none';

        if (type === 'commander') {
            checkCommanderRelations(commander.id);
        }
    }

    async function populateSuggestions(type) {
        const config = FIELD_CONFIG[type];
        if (!config) return;

        const inputElement = document.getElementById(config.inputId);
        const suggestionsListElement = document.getElementById(config.suggestionsId);
        const query = inputElement.value.trim();

        suggestionsListElement.innerHTML = "";

        if (query.length < 1) {
            suggestionsListElement.style.display = "none";
            return;
        }

        suggestionsListElement.style.display = "block";
        const loadingItem = document.createElement("li");
        loadingItem.className = "px-4 py-2 text-center text-sm text-violet-500 dark:text-violet-400";
        loadingItem.textContent = "Loading...";
        suggestionsListElement.appendChild(loadingItem);
        adjustSuggestionsList(suggestionsListElement, inputElement);

        try {
            const commanders = await searchCommanders(query, type);
            suggestionsListElement.innerHTML = "";

            if (commanders.length === 0) {
                const noResults = document.createElement("li");
                noResults.className = "px-4 py-2 text-center text-sm text-violet-500 dark:text-violet-400";
                noResults.textContent = "No results";
                suggestionsListElement.appendChild(noResults);
                return;
            }

            commanders.forEach(card => { // Renamed to 'card' for clarity, as it's a card object
                 if (type !== 'commander' && card.id === selectedCommanderId) {
                    return; 
                }
                const item = document.createElement("li");
                item.className = "px-4 py-2 hover:bg-violet-100 dark:hover:bg-violet-700 cursor-pointer flex items-center text-sm text-gray-700 dark:text-gray-200";
                item.innerHTML = card.image
                    ? `<img src="${card.image}" alt="${card.name}" class="w-8 h-10 mr-2 object-contain rounded-sm"> <span class="truncate">${card.name}</span>`
                    : `<span class="truncate">${card.name}</span>`;
                item.addEventListener("click", () => {
                    handleSuggestionClick(type, card, suggestionsListElement);
                });
                suggestionsListElement.appendChild(item);
            });
        } catch (error) {
            console.error(`Error populating suggestions for ${type}:`, error.message);
            suggestionsListElement.innerHTML = "";
            const errorItem = document.createElement("li");
            errorItem.className = "px-4 py-2 text-center text-sm text-red-500 dark:text-red-400";
            errorItem.textContent = "Error loading suggestions";
            suggestionsListElement.appendChild(errorItem);
        }
    }

    function adjustSuggestionsList(suggestionsList, inputElement) {
        const inputRect = inputElement.getBoundingClientRect();
        suggestionsList.style.minWidth = `${inputRect.width}px`;
    }

    const debouncedPopulateSuggestions = debounce(populateSuggestions, 300);

    function handleSearchInput(type, event) {
        const config = FIELD_CONFIG[type];
        if(!config) return;
         if (event.target.value.trim() === '') {
            // Use the camelCase key directly from FIELD_CONFIG
            delete event.target.dataset[config.datasetKey]; 
            if(type === 'commander') {
                 selectedCommanderId = null;
                 hideAllAssociatedFields();
            }
        }
        debouncedPopulateSuggestions(type);
    }

    // --- Event Listener Setup for Dynamic Fields ---
    conditionalFieldPrefixes.forEach(type => {
        const config = FIELD_CONFIG[type];
        const inputElement = document.getElementById(config.inputId);
        const suggestionsListElement = document.getElementById(config.suggestionsId);

        if (inputElement && suggestionsListElement) {
             inputElement.addEventListener("input", (event) => handleSearchInput(type, event));
             inputElement.addEventListener("focus", () => {
                if (inputElement.value.trim().length > 0) {
                    debouncedPopulateSuggestions(type);
                }
             });
             document.addEventListener("click", function(event) {
                if (inputElement.parentElement && !inputElement.parentElement.contains(event.target) && 
                    suggestionsListElement.parentElement && !suggestionsListElement.parentElement.contains(event.target)) {
                     suggestionsListElement.style.display = "none";
                }
            });
        } else {
            console.warn(`Deck form: Input or suggestions element not found for type: ${type}. Check IDs: ${config.inputId}, ${config.suggestionsId}`);
        }
    });
});

// --- Exports ---
export { FIELD_CONFIG, conditionalFieldPrefixes }; // Exporting both as new-deck-modal.js uses conditionalFieldPrefixes