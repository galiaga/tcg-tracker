import { loadDeckTypes } from '../../deck_types.js';
import { clearTagInput, initializeTagInput as initializeRegisterDeckTagInput } from '../../registerDeck.js'; // Renamed import to avoid conflict

document.addEventListener("DOMContentLoaded", () => {
    const modal = document.getElementById("newDeckModal");
    if (!modal) return;

    const modalContent = modal.querySelector(".bg-white");
    const openBtn = document.getElementById("newDeckModalButton");
    const closeBtn = document.getElementById("newDeckModalCloseButton");
    const form = document.getElementById('register-deck-form');

    if (!modalContent || !openBtn || !closeBtn || !form) return;

    const conditionalFieldPrefixes = [
        "commander", "partner", "friendsForever",
        "doctorCompanion", "timeLordDoctor", "chooseABackground"
    ];

    const tagInputContainerId = 'deck-tags-container';
    const tagInputElementId = 'deck-tags-input';
    const tagSuggestionsId = 'deck-tags-suggestions';

    // --- Reset Logic ---
    function resetNewDeckForm() {
        form.reset();

        const select = document.getElementById("deck_type");
        if (select) {
            select.value = "";
        }

        conditionalFieldPrefixes.forEach(prefix => {
            const fieldDiv = document.getElementById(`${prefix}Field`);
            const inputElement = document.getElementById(`${prefix}_name`);
            const suggestionsUl = document.getElementById(`${prefix}-suggestions`);

            if (fieldDiv) {
                fieldDiv.style.display = 'none';
                fieldDiv.classList.add('hidden');
            }
            if (inputElement) {
                const datasetKey = Object.keys(inputElement.dataset)[0];
                if (datasetKey) {
                    delete inputElement.dataset[datasetKey];
                }
                inputElement.value = '';
            }
            if (suggestionsUl) {
                suggestionsUl.innerHTML = '';
                suggestionsUl.style.display = 'none';
            }
        });

        // --- Tag Input Reset ---
        if (typeof clearTagInput === 'function') {
            try {
                clearTagInput();
            } catch (err) {
                console.error("Error calling imported clearTagInput:", err);
                manualClearTagInput();
            }
        } else {
            manualClearTagInput();
        }
    }

    function manualClearTagInput() {
         const tagContainer = document.getElementById(tagInputContainerId);
         const tagInput = document.getElementById(tagInputElementId);
         const tagSuggestions = document.getElementById(tagSuggestionsId);
         if (tagContainer) tagContainer.innerHTML = '';
         if (tagInput) tagInput.value = '';
         if (tagSuggestions) {
             tagSuggestions.innerHTML = '';
             tagSuggestions.classList.add('hidden');
         }
    }

    // --- Modal Lifecycle ---
    function openModal() {
        modal.classList.remove("hidden");
        modal.classList.add("flex");

        loadDeckTypes();
        resetNewDeckForm(); // Reset state before showing
        initializeTagInput(); // Initialize tags after reset

        setTimeout(() => {
            modalContent.classList.remove("scale-95", "opacity-0");
            modalContent.classList.add("scale-100", "opacity-100");
        }, 10);
    }

    function closeModal() {
        modalContent.classList.remove("scale-100", "opacity-100");
        modalContent.classList.add("scale-95", "opacity-0");

        setTimeout(() => {
            modal.classList.add("hidden");
            modal.classList.remove("flex");
            resetNewDeckForm(); // Reset state after hiding
        }, 150);
    }

    // --- Tag Input Handling (Initialization within Modal Context) ---
    function initializeTagInput() {
        // Use the initialization function potentially imported from registerDeck.js
        // This assumes registerDeck.js sets up the TagInputManager instance
        if (typeof initializeRegisterDeckTagInput === 'function') {
             try {
                 initializeRegisterDeckTagInput();
                 // Ensure tags are cleared by the reset logic, but call clear here too if needed
                 // clearTagInput(); // Called within resetNewDeckForm now
             } catch (err) {
                 console.error("Error calling imported initializeRegisterDeckTagInput:", err);
             }
        } else {
             console.warn("initializeRegisterDeckTagInput function not imported.");
             // If TagInputManager is global, you might initialize directly here as a fallback
             // if (typeof TagInputManager !== 'undefined') { ... }
        }
    }

    // --- Event Listeners ---
    openBtn.addEventListener("click", openModal);
    closeBtn.addEventListener("click", closeModal);

    modal.addEventListener("click", (event) => {
        if (event.target === modal) {
            closeModal();
        }
    });

    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && !modal.classList.contains('hidden')) {
            closeModal();
        }
    });
});