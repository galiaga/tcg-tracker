import { authFetch } from './auth/auth.js';

document.addEventListener("DOMContentLoaded", function () {
    loadDeckTypes();
});

async function loadDeckTypes() {
    try {
        const token = localStorage.getItem("access_token");
        if (!token) {
            showFlashMessage("You need to log in to load deck types", "warning");
            return;
        }

        let response = await authFetch("/api/deck_types", {
            method: "GET",
            headers: {
                "Authorization": `Bearer ${token}`,
                "Content-Type": "application/json"
            }
        });

        if (!response) return;

        if (!response.ok) throw new Error("Error loading deck types");

        let deckTypes = await response.json();
        let select = document.getElementById("deck_type");

        select.innerHTML = '<option value="" disabled selected>Select a deck type</option>';
        deckTypes.forEach(type => {
            let option = document.createElement("option");
            option.value = type.id;
            option.textContent = type.deck_type;
            select.appendChild(option);
        });

    } catch (error) {
        showFlashMessage(error.message, "danger");
    }
}
