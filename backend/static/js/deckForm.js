import { searchCommander } from "./api/index.js";

const COMMANDER_ID = "7";

document.addEventListener("DOMContentLoaded", function () {
    const deckTypeSelect = document.getElementById("deck_type");
    const commanderField = document.getElementById("commanderField");
    const commanderInput = document.getElementById("commander_name");

    const partnerField = document.getElementById("partnerField");
    const friendsForeverField = document.getElementById("friendsForeverField");
    const doctorCompanionField = document.getElementById("doctorCompanionField");
    const timeLordDoctorField = document.getElementById("timeLordDoctorField");
    const backgroundField = document.getElementById("backgroundField");
    const chooseABackgroundField = document.getElementById("chooseABackgroundField")
    
    let selectedCommanderId = null; 

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

    async function checkCommanderRelations(commanderId) {
        const token = localStorage.getItem("access_token");

        if (!token) {
            console.error("No hay token en localStorage.");
            return;
        }

        const response = await fetch(`/api/get_commander_attributes?q=${commanderId}`, {
            method: "GET",
            headers: {
                "Authorization": `Bearer ${token}`,
                "Content-Type": "application/json"
            }
        });

        if (!response.ok) {
            console.error("Request error:", response.status);
            return;
        }

        const commanderData = await response.json();

        selectedCommanderId = commanderData.id;

        console.log("Datos del comandante recibidos:", commanderData, "END DE DATOS");

        partnerField.style.display = "none";
        friendsForeverField.style.display = "none";
        doctorCompanionField.style.display = "none";
        timeLordDoctorField.style.display = "none";
        backgroundField.style.display = "none";
        chooseABackgroundField.style.display = "none";

        if (commanderData.partner) {
            partnerField.style.display = "block";
            document.getElementById("partner_name").placeholder = "Who is the Partner?";
            await populateSuggestions("partner");
        }

        if (commanderData.friends_forever) {
            friendsForeverField.style.display = "block";
            document.getElementById("friendsForever_name").placeholder = "Who is the BFF?";
            await populateSuggestions("friendsForever");
        }

        if (commanderData.doctor_companion) {
            doctorCompanionField.style.display = "block";
            document.getElementById("doctorCompanion_name").placeholder = "Who is the Doctor?";
            await populateSuggestions("doctorCompanion");
        }

        if (commanderData.time_lord_doctor) {
            timeLordDoctorField.style.display = "block";
            document.getElementById("timeLordDoctor_name").placeholder = "Who is the Doctor's Companion?";
            await populateSuggestions("timeLordDoctor");
        }

        if (commanderData.background) {
            backgroundField.style.display = "block";
            document.getElementById("background_name").placeholder = "Choose a commander";
            await populateSuggestions("background");
        }

        if (commanderData.choose_a_background) {
            chooseABackgroundField.style.display = "block";
            document.getElementById("chooseABackground_name").placeholder = "Choose a Background";
            await populateSuggestions("chooseABackground");
        }

    }

    async function populateSuggestions(type) {
        let query;
        if (type === "partner") {
            query = document.getElementById("partner_name").value.trim();
        } else if (type === "friendsForever") {
            query = document.getElementById("friendsForever_name").value.trim();
        } else if (type === "doctorCompanion") {
            query = document.getElementById("doctorCompanion_name").value.trim();
        } else if (type === "timeLordDoctor") {
            query = document.getElementById("timeLordDoctor_name").value.trim();
        } else if (type === "background") {
            query = document.getElementById("background_name").value.trim();
        } else if (type === "chooseABackground") {
            query = document.getElementById("chooseABackground_name").value.trim();
        } else {
            query = document.getElementById("commander_name").value.trim();
        }

        const response = await fetch(`/api/search_commanders?q=${query}&type=${type}`);
        const commanders = await response.json();
        const suggestionMap = {
            partner: "partner-suggestions",
            friendsForever: "friendsForever-suggestions",
            doctorCompanion: "doctorCompanion-suggestions",
            timeLordDoctor: "timeLordDoctor-suggestions",
            background: "background-suggestions",
            chooseABackground: "chooseABackground-suggestions"
        };
        
        const suggestionsList = document.getElementById(suggestionMap[type]);

        suggestionsList.innerHTML = '';

        commanders.forEach(commander => {
            if (commander.id === selectedCommanderId) return;

            const listItem = document.createElement("li");
            listItem.classList.add("list-group-item");
            listItem.textContent = commander.name;
            listItem.addEventListener("click", () => {
                const inputIds = {
                    partner: "partner_name",
                    friendsForever: "friendsForever_name",
                    doctorCompanion: "doctorCompanion_name",
                    timeLordDoctor: "timeLordDoctor_name",
                    background: "background_name",
                    chooseABackground: "chooseABackground_name"
                };
            
                const inputId = inputIds[type];
                if (inputId) {
                    document.getElementById(inputId).value = commander.name;
                }

                suggestionsList.innerHTML = '';
            });
            suggestionsList.appendChild(listItem);
        });

        if (commanders.length === 0) {
            const noResults = document.createElement("li");
            noResults.classList.add("list-group-item", "text-center");
            noResults.textContent = "No results";
            suggestionsList.appendChild(noResults);
        }
    }

    const commanderSuggestions = document.getElementById("commander-suggestions");

    commanderSuggestions.style.display = "none";

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
        loadingItem.textContent = "Loading...";
        commanderSuggestions.appendChild(loadingItem);
        
        if (this.searchTimeout) clearTimeout(this.searchTimeout);
        
        this.searchTimeout = setTimeout(async () => {
            const commanders = await searchCommander(query); 
            commanderSuggestions.innerHTML = "";
            
            if (commanders.length === 0) {
                const noResults = document.createElement("li");
                noResults.classList.add("list-group-item", "text-center");
                noResults.textContent = "No results";
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
                    checkCommanderRelations(commander.id);
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

    function adjustSuggestionsList(suggestionsList, inputElement) {
        const inputRect = inputElement.getBoundingClientRect();
        const inputWidth = inputElement.offsetWidth;
    
        suggestionsList.style.minWidth = `${inputWidth}px`;
        suggestionsList.style.left = '50%';
        suggestionsList.style.transform = 'translateX(-50%)';
    }

    const partnerInput = document.getElementById("partner_name");
    partnerInput.addEventListener("input", function() {
        const query = partnerInput.value.trim();
        const partnerSuggestions = document.getElementById("partner-suggestions");
        partnerSuggestions.innerHTML = "";

        if (query.length < 1) {
            partnerSuggestions.style.display = "none";
            return;
        }

        partnerSuggestions.style.display = "block";
        
        const loadingItem = document.createElement("li");
        loadingItem.classList.add("list-group-item", "text-center");
        loadingItem.textContent = "Loading...";
        partnerSuggestions.appendChild(loadingItem);

        if (this.searchTimeout) clearTimeout(this.searchTimeout);
        
        this.searchTimeout = setTimeout(async () => {
            await populateSuggestions("partner");
        }, 100);
    });

    const friendsForeverInput = document.getElementById("friendsForever_name");
    friendsForeverInput.addEventListener("input", function() {
        const query = friendsForeverInput.value.trim();
        const friendsForeverSuggestions = document.getElementById("friendsForever-suggestions");
        friendsForeverSuggestions.innerHTML = "";

        if (query.length < 1) {
            friendsForeverSuggestions.style.display = "none";
            return;
        }

        friendsForeverSuggestions.style.display = "block";
        
        const loadingItem = document.createElement("li");
        loadingItem.classList.add("list-group-item", "text-center");
        loadingItem.textContent = "Loading...";
        friendsForeverSuggestions.appendChild(loadingItem);

        if (this.searchTimeout) clearTimeout(this.searchTimeout);
        
        this.searchTimeout = setTimeout(async () => {
            await populateSuggestions("friendsForever");
        }, 100);
    });

    const doctorCompanionInput = document.getElementById("doctorCompanion_name");
    doctorCompanionInput.addEventListener("input", function() {
        const query = doctorCompanionInput.value.trim();
        const doctorCompanionSuggestions = document.getElementById("doctorCompanion-suggestions");
        doctorCompanionSuggestions.innerHTML = "";

        if (query.length < 1) {
            doctorCompanionSuggestions.style.display = "none";
            return;
        }

        doctorCompanionSuggestions.style.display = "block";
        
        const loadingItem = document.createElement("li");
        loadingItem.classList.add("list-group-item", "text-center");
        loadingItem.textContent = "Loading...";
        doctorCompanionSuggestions.appendChild(loadingItem);

        if (this.searchTimeout) clearTimeout(this.searchTimeout);
        
        this.searchTimeout = setTimeout(async () => {
            await populateSuggestions("doctorCompanion");
        }, 100);
    });

    const timeLordDoctorInput = document.getElementById("timeLordDoctor_name");
    timeLordDoctorInput.addEventListener("input", function() {
        const query = timeLordDoctorInput.value.trim();
        const timeLordDoctorSuggestions = document.getElementById("timeLordDoctor-suggestions");
        timeLordDoctorSuggestions.innerHTML = "";

        if (query.length < 1) {
            timeLordDoctorSuggestions.style.display = "none";
            return;
        }

        timeLordDoctorSuggestions.style.display = "block";
        
        const loadingItem = document.createElement("li");
        loadingItem.classList.add("list-group-item", "text-center");
        loadingItem.textContent = "Loading...";
        timeLordDoctorSuggestions.appendChild(loadingItem);

        if (this.searchTimeout) clearTimeout(this.searchTimeout);
        
        this.searchTimeout = setTimeout(async () => {
            await populateSuggestions("timeLordDoctor");
        }, 100);
    });

    const backgroundInput = document.getElementById("background_name");
    backgroundInput.addEventListener("input", function() {
        const query = backgroundInput.value.trim();
        const backgroundSuggestions = document.getElementById("background-suggestions");
        backgroundSuggestions.innerHTML = "";

        if (query.length < 1) {
            backgroundSuggestions.style.display = "none";
            return;
        }

        backgroundSuggestions.style.display = "block";
        
        const loadingItem = document.createElement("li");
        loadingItem.classList.add("list-group-item", "text-center");
        loadingItem.textContent = "Loading...";
        backgroundSuggestions.appendChild(loadingItem);

        if (this.searchTimeout) clearTimeout(this.searchTimeout);
        
        this.searchTimeout = setTimeout(async () => {
            await populateSuggestions("background");
        }, 100);
    });

    const chooseABackgroundInput = document.getElementById("chooseABackground_name");
    chooseABackgroundInput.addEventListener("input", function() {
        const query = chooseABackgroundInput.value.trim();
        const chooseABackgroundSuggestions = document.getElementById("chooseABackground-suggestions");
        chooseABackgroundSuggestions.innerHTML = "";

        if (query.length < 1) {
            chooseABackgroundSuggestions.style.display = "none";
            return;
        }

        chooseABackgroundSuggestions.style.display = "block";
        
        const loadingItem = document.createElement("li");
        loadingItem.classList.add("list-group-item", "text-center");
        loadingItem.textContent = "Loading...";
        chooseABackgroundSuggestions.appendChild(loadingItem);

        if (this.searchTimeout) clearTimeout(this.searchTimeout);
        
        this.searchTimeout = setTimeout(async () => {
            await populateSuggestions("chooseABackground");
        }, 100);
    });
});
