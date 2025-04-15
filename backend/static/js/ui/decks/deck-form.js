import { searchCommander } from "../../api/index.js";
import { authFetch } from "../../auth/auth.js";

const COMMANDER_DECK_TYPE_ID = "7";

const FIELD_CONFIG = {
    commander: {
        inputId: "commander_name",
        suggestionsId: "commander-suggestions",
        fieldId: "commanderField",
        datasetKey: "commanderId"
    },
    partner: {
        inputId: "partner_name",
        suggestionsId: "partner-suggestions",
        fieldId: "partnerField",
        datasetKey: "partnerId"
    },
    friendsForever: {
        inputId: "friendsForever_name",
        suggestionsId: "friendsForever-suggestions",
        fieldId: "friendsForeverField",
        datasetKey: "friendsForeverId"
    },
    doctorCompanion: {
        inputId: "doctorCompanion_name",
        suggestionsId: "doctorCompanion-suggestions",
        fieldId: "doctorCompanionField",
        datasetKey: "timeLordDoctorId"
    },
    timeLordDoctor: {
        inputId: "timeLordDoctor_name",
        suggestionsId: "timeLordDoctor-suggestions",
        fieldId: "timeLordDoctorField",
        datasetKey: "doctorCompanionId"
    },
    chooseABackground: {
        inputId: "chooseABackground_name",
        suggestionsId: "chooseABackground-suggestions",
        fieldId: "chooseABackgroundField",
        datasetKey: "backgroundId"
    }
};

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

document.addEventListener("DOMContentLoaded", function () {
    const deckTypeSelect = document.getElementById("deck_type");
    const commanderInput = document.getElementById(FIELD_CONFIG.commander.inputId);
    const commanderSuggestions = document.getElementById(FIELD_CONFIG.commander.suggestionsId);
    const commanderField = document.getElementById(FIELD_CONFIG.commander.fieldId);

    let selectedCommanderId = null;
    const searchTimeouts = {};

    if (!deckTypeSelect || !commanderField || !commanderInput) {
        console.error("Essential form elements (deck type, commander field/input) not found.");
        return;
    }

    deckTypeSelect.addEventListener("change", function () {
        const showCommander = this.value === COMMANDER_DECK_TYPE_ID;
        commanderField.style.display = showCommander ? "block" : "none";
        if (!showCommander) {
            commanderInput.value = "";
            commanderInput.removeAttribute(`data-${FIELD_CONFIG.commander.datasetKey.toLowerCase()}`);
            selectedCommanderId = null;
            hideAllAssociatedFields();
        }
    });

    function hideAllAssociatedFields() {
        Object.keys(FIELD_CONFIG).forEach(type => {
            if (type !== 'commander') {
                const config = FIELD_CONFIG[type];
                const fieldElement = document.getElementById(config.fieldId);
                const inputElement = document.getElementById(config.inputId);
                if (fieldElement) {
                    fieldElement.style.display = "none";
                }
                 if (inputElement) {
                     inputElement.value = '';
                     inputElement.removeAttribute(`data-${config.datasetKey.toLowerCase()}`);
                }
            }
        });
    }

    async function checkCommanderRelations(commanderId) {
        const token = localStorage.getItem("access_token");
        if (!token) {
            console.error("Token not found in localStorage.");
            return;
        }

        hideAllAssociatedFields();

        try {
            const apiUrl = `/api/get_commander_attributes?q=${commanderId}`;
            const response = await authFetch(apiUrl);
            if (!response) throw new Error("Authentication or network error occurred.");
            if (!response.ok) {
                console.error("Error fetching commander attributes:", response.status, response.statusText);
                return;
            }

            const commanderData = await response.json();
            selectedCommanderId = commanderData.id;

            if (commanderData.partner) showAssociatedField('partner');
            if (commanderData.friends_forever) showAssociatedField('friendsForever');
            if (commanderData.doctor_companion) showAssociatedField('doctorCompanion');
            if (commanderData.time_lord_doctor) showAssociatedField('timeLordDoctor');
            if (commanderData.choose_a_background) showAssociatedField('chooseABackground');

        } catch (error) {
            console.error("Network error while fetching attributes:", error);
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

    function handleSuggestionClick(type, commander, suggestionsListElement) {
        const config = FIELD_CONFIG[type];
        if (!config) return;

        const inputElement = document.getElementById(config.inputId);

        inputElement.value = commander.name;
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
        loadingItem.className = "px-4 py-2 text-center text-violet-500";
        loadingItem.textContent = "Loading...";
        suggestionsListElement.appendChild(loadingItem);
        adjustSuggestionsList(suggestionsListElement, inputElement);

        try {
            const response = await fetch(`/api/search_commanders?q=${encodeURIComponent(query)}&type=${type}`);
            if (!response.ok) {
                throw new Error(`API search_commanders error: ${response.status}`);
            }
            const commanders = await response.json();

            suggestionsListElement.innerHTML = "";

            if (commanders.length === 0) {
                const noResults = document.createElement("li");
                noResults.className = "px-4 py-2 text-center text-violet-500";
                noResults.textContent = "No results";
                suggestionsListElement.appendChild(noResults);
                return;
            }

            commanders.forEach(commander => {
                if (type !== 'commander' && commander.id === selectedCommanderId) {
                    return;
                }

                const item = document.createElement("li");
                item.className = "px-4 py-2 hover:bg-violet-100 cursor-pointer flex items-center";
                item.innerHTML = commander.image
                    ? `<img src="${commander.image}" alt="${commander.name}" class="w-8 h-10 mr-2 object-contain"> ${commander.name}`
                    : commander.name;

                item.addEventListener("click", () => {
                    handleSuggestionClick(type, commander, suggestionsListElement);
                });
                suggestionsListElement.appendChild(item);
            });

        } catch (error) {
            console.error(`Error populating suggestions for ${type}:`, error);
            suggestionsListElement.innerHTML = "";
            const errorItem = document.createElement("li");
            errorItem.className = "px-4 py-2 text-center text-red-500";
            errorItem.textContent = "Error loading suggestions";
            suggestionsListElement.appendChild(errorItem);
        }
    }

    function adjustSuggestionsList(suggestionsList, inputElement) {
        const inputWidth = inputElement.offsetWidth;
        suggestionsList.style.minWidth = `${inputWidth}px`;
    }

    const debouncedPopulateSuggestions = debounce(populateSuggestions, 300);

    function handleSearchInput(type, event) {
        const config = FIELD_CONFIG[type];
        if(!config) return;
         if (event.target.value.trim() === '') {
            event.target.removeAttribute(`data-${config.datasetKey.toLowerCase()}`);
            if(type === 'commander') {
                 selectedCommanderId = null;
                 hideAllAssociatedFields();
            }
        }
        debouncedPopulateSuggestions(type);
    }

    Object.keys(FIELD_CONFIG).forEach(type => {
        const config = FIELD_CONFIG[type];
        const inputElement = document.getElementById(config.inputId);
        const suggestionsListElement = document.getElementById(config.suggestionsId);

        if (inputElement && suggestionsListElement) {
             inputElement.addEventListener("input", (event) => handleSearchInput(type, event));

             document.addEventListener("click", function(event) {
                if (inputElement && suggestionsListElement && !inputElement.contains(event.target) && !suggestionsListElement.contains(event.target)) {
                     suggestionsListElement.style.display = "none";
                }
            });
        } else {
            console.warn(`Input or suggestions element not found for type: ${type}`);
        }
    });

});