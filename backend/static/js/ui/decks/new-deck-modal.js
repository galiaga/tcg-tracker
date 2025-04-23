import { loadDeckTypes } from '../../deck_types.js';
import { conditionalFieldPrefixes, FIELD_CONFIG } from './deck-form.js'; // Import shared config
import { TagInputManager } from '../tagInput.js'; // Import Tag Manager

document.addEventListener("DOMContentLoaded", () => {
    const modal = document.getElementById("newDeckModal");
    if (!modal) return;

    const modalContent = modal.querySelector(".bg-white");
    const openBtn = document.getElementById("newDeckModalButton");
    const closeBtn = document.getElementById("newDeckModalCloseButton");
    const form = document.getElementById('register-deck-form');

    if (!modalContent || !openBtn || !closeBtn || !form) return;

    // --- Tag Input Management ---
    let deckTagInputInstance = null; // Instance managed by this modal script
    const tagInputContainerId = 'deck-tags-container';
    const tagInputElementId = 'deck-tags-input';
    const tagSuggestionsId = 'deck-tags-suggestions';

    function initializeTagInput() {
        if (typeof TagInputManager !== 'undefined') {
            if (!deckTagInputInstance) { // Initialize only once per page load potentially
                 try {
                    deckTagInputInstance = TagInputManager.init({
                        inputId: tagInputElementId,
                        suggestionsId: tagSuggestionsId,
                        containerId: tagInputContainerId
                    });
                    // Attach instance to form for access during submission
                    if (deckTagInputInstance) {
                        form.tagInputInstance = deckTagInputInstance;
                    } else {
                         console.error("Failed to initialize TagInputManager for decks.");
                    }
                 } catch (err) {
                     console.error("Error initializing TagInputManager:", err);
                 }
            }
            // Always clear tags when initializing/re-initializing for modal open
            if (deckTagInputInstance) {
                deckTagInputInstance.clearTags();
            }
        } else {
             console.warn("TagInputManager not loaded when new-deck-modal.js attempted init.");
        }
    }

    function clearTagInput() {
        if (deckTagInputInstance) {
            try {
                deckTagInputInstance.clearTags();
            } catch (err) {
                console.error("Error clearing tags:", err);
            }
        } else {
            // Manual fallback if instance somehow got lost (shouldn't happen often)
            const tagContainer = document.getElementById(tagInputContainerId);
            const tagInput = document.getElementById(tagInputElementId);
            if (tagContainer) tagContainer.innerHTML = '';
            if (tagInput) tagInput.value = '';
        }
    }

    // --- Reset Logic ---
    function resetNewDeckForm() {
        form.reset(); // Resets standard inputs, textareas, selects

        const select = document.getElementById("deck_type");
        if (select) {
            select.value = ""; // Explicitly set select to default value
        }

        // Use imported prefixes to reset dynamic fields
        conditionalFieldPrefixes.forEach(prefix => {
            const config = FIELD_CONFIG[prefix]; // Use imported config
            if (!config) return;

            const fieldDiv = document.getElementById(config.fieldId);
            const inputElement = document.getElementById(config.inputId);
            const suggestionsUl = document.getElementById(config.suggestionsId);

            if (fieldDiv) {
                fieldDiv.style.display = 'none'; // Force hide using style
                // Optionally ensure hidden class is also present if your CSS relies on it
                // fieldDiv.classList.add('hidden');
            }
            if (inputElement) {
                // Clear any potential dataset value (form.reset might not clear dataset)
                 const datasetKey = config.datasetKey.toLowerCase();
                 if (inputElement.dataset[datasetKey]) {
                     delete inputElement.dataset[datasetKey];
                 }
                 // Ensure value is clear (form.reset should handle this, but belt-and-suspenders)
                 inputElement.value = '';
            }
            if (suggestionsUl) {
                suggestionsUl.innerHTML = ''; // Clear suggestions
                suggestionsUl.style.display = 'none'; // Hide suggestions list
            }
        });

        // Clear tags using the instance managed by this script
        clearTagInput();
    }

    // --- Modal Lifecycle ---
    function openModal() {
        modal.classList.remove("hidden");
        modal.classList.add("flex");

        loadDeckTypes(); // Load dynamic select options
        resetNewDeckForm(); // Reset form to default state FIRST
        initializeTagInput(); // Initialize tag input AFTER reset

        // Start animation
        setTimeout(() => {
            modalContent.classList.remove("scale-95", "opacity-0");
            modalContent.classList.add("scale-100", "opacity-100");
        }, 10);
    }

    function closeModal() {
        // Start animation
        modalContent.classList.remove("scale-100", "opacity-100");
        modalContent.classList.add("scale-95", "opacity-0");

        // Hide modal and reset form AFTER animation
        setTimeout(() => {
            modal.classList.add("hidden");
            modal.classList.remove("flex");
            resetNewDeckForm(); // Ensure clean state for next open
        }, 150); // Match CSS transition duration
    }

    // --- Event Listeners ---
    openBtn.addEventListener("click", openModal);
    closeBtn.addEventListener("click", closeModal);

    modal.addEventListener("click", (event) => {
        if (event.target === modal) { // Click on backdrop
            closeModal();
        }
    });

    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && !modal.classList.contains('hidden')) {
            closeModal();
        }
    });
});