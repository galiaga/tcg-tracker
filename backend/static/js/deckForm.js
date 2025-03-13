import { searchCommander } from "./api/index.js";

const COMMANDER_ID = "4";

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

    const commanderSuggestions = document.createElement("ul"); 
    commanderSuggestions.classList.add("list-group", "position-absolute", "w-100");
    commanderInput.parentNode.appendChild(commanderSuggestions);

    commanderInput.addEventListener("input", async function () {
        const query = commanderInput.value.trim();
        commanderSuggestions.innerHTML = "";
    
        if (query.length < 1) return;
    
        const commanders = await searchCommander(query);
    
        commanders.slice(0, 10).forEach(commander => {
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
    });    

    document.addEventListener("click", function (event) {
        if (!commanderInput.contains(event.target) && !commanderSuggestions.contains(event.target)) {
            commanderSuggestions.innerHTML = "";
        }
    });
});
