import { searchCommander } from "./api/index.js";

const COMMANDER_ID = "7";

document.addEventListener("DOMContentLoaded", function () {
    const deckTypeSelect = document.getElementById("deck_type");
    const commanderField = document.getElementById("commander_field");
    const commanderInput = document.getElementById("commander_name");

    if (!deckTypeSelect || !commanderField || !commanderInput) {
        console.error("Uno o más elementos del formulario no fueron encontrados.");
        return;
    }

    deckTypeSelect.addEventListener("change", function () {
        if (this.value === COMMANDER_ID) {
            commanderField.style.display = "block";
        } else {
            commanderField.style.display = "none";
            commanderInput.value = "";
        }
    });

    const commanderSuggestions = document.getElementById("commander-suggestions");

    commanderSuggestions.style.display = "none";

    function adjustSuggestionsList(suggestionsList, inputElement) {
        const inputRect = inputElement.getBoundingClientRect();
        const inputWidth = inputElement.offsetWidth;
        
        suggestionsList.style.minWidth = `${inputWidth}px`;
        
        suggestionsList.style.left = '50%';
        suggestionsList.style.transform = 'translateX(-50%)';
    }

    commanderInput.addEventListener("input", function() {
        const query = commanderInput.value.trim();
        commanderSuggestions.innerHTML = "";
        
        if (query.length < 1) {
            commanderSuggestions.style.display = "none";
            return;
        }

        commanderSuggestions.style.display = "block";
        
        const loadingItem = document.createElement("li");
        loadingItem.classList.add("list-group-item", "text-center");
        loadingItem.textContent = "Buscando...";
        commanderSuggestions.appendChild(loadingItem);
        
        if (this.searchTimeout) clearTimeout(this.searchTimeout);
        
        this.searchTimeout = setTimeout(async () => {
            const commanders = await searchCommander(query);
            commanderSuggestions.innerHTML = "";
            
            if (commanders.length === 0) {
                const noResults = document.createElement("li");
                noResults.classList.add("list-group-item", "text-center");
                noResults.textContent = "No se encontraron resultados";
                commanderSuggestions.appendChild(noResults);
                return;
            }
            
            commanders.forEach(commander => {
                const item = document.createElement("li");
                item.classList.add("list-group-item", "list-group-item-action", "d-flex", "align-items-center");
                item.innerHTML = commander.image
                    ? `<img src="${commander.image}" class="me-2" width="30" height="40"> ${commander.name}`
                    : commander.name;
                
                item.addEventListener("click", () => {
                    commanderInput.value = commander.name;
                    commanderInput.dataset.commanderId = commander.id;
                    commanderSuggestions.innerHTML = "";
                });
                
                commanderSuggestions.appendChild(item);
            });

            document.addEventListener("click", function(event) {
                if (!commanderInput.contains(event.target) && !commanderSuggestions.contains(event.target)) {
                    commanderSuggestions.style.display = "none";
                }
            });

            adjustSuggestionsList(commanderSuggestions, commanderInput);
        }, 100);
    });

});
