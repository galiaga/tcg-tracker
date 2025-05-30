import { authFetch } from './auth/auth.js';

export async function loadDeckTypes() {
    try {


        const apiUrl = `/api/deck_types`;
        const response = await authFetch(apiUrl); 

        if (!response) {
            return; 
        }
        if (response.status === 401) {
             return;
        }


        if (!response.ok) {
             let errorMsg = `Error loading deck types (Status: ${response.status})`;
             try {
                 const errorData = await response.json();
                 errorMsg = errorData.error || errorMsg;
             } catch(e) { /* Ignore if body isn't JSON */ }
             throw new Error(errorMsg);
        }

        // --- Process successful response ---
        let deckTypes = await response.json();
        let select = document.getElementById("deck_type");

        if (select) {
            select.innerHTML = '<option value="" disabled selected>Select a deck type</option>';
            deckTypes.forEach(type => {
                let option = document.createElement("option");
                option.value = type.id;
                option.textContent = type.deck_type || type.name; 
                select.appendChild(option);
            });
        } else {
            console.warn("Deck type select element (#deck_type) not found on this page.");
        }


    } catch (error) {
        console.error("Error in loadDeckTypes:", error); 
        showFlashMessage(error.message || "Failed to load deck types.", "danger");
    }
}