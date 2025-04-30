// backend/static/js/profile/update_profile.js

import { authFetch } from '../auth/auth.js';
// Assuming showFlashMessage is globally available via another script or base template
// If not, you might need to import it or define it here.
// Example: import { showFlashMessage } from '../ui/flashMessages.js';

console.log("update_profile.js: Script loaded."); // For debugging

document.addEventListener('DOMContentLoaded', () => {
    console.log("update_profile.js: DOMContentLoaded event fired."); // For debugging

    // --- Get DOM Elements ---
    const profileForm = document.getElementById('update-profile-form');
    const firstNameInput = document.getElementById('first_name');
    const lastNameInput = document.getElementById('last_name');
    const usernameInput = document.getElementById('username');
    const editButton = document.getElementById('edit-profile-button');
    const saveButton = document.getElementById('save-profile-button'); // The submit button
    const cancelButton = document.getElementById('cancel-profile-button');

    // --- Log element finding results ---
    console.log("update_profile.js: profileForm found?", !!profileForm);
    console.log("update_profile.js: editButton found?", !!editButton);
    console.log("update_profile.js: saveButton found?", !!saveButton);
    console.log("update_profile.js: cancelButton found?", !!cancelButton);
    // --- End log ---

    // Check if all essential elements exist before proceeding
    if (!profileForm || !firstNameInput || !lastNameInput || !usernameInput || !editButton || !saveButton || !cancelButton) {
        console.warn("update_profile.js: One or more profile form elements not found. Edit/Save/Cancel logic not fully initialized.");
        return; // Stop execution if elements are missing
    }

    // Store references to the inputs that will be toggled
    const editableInputs = [firstNameInput, lastNameInput, usernameInput];

    // Store original values when editing starts
    let originalValues = {};

    // --- Mode Management Functions ---

    /**
     * Stores the current values of the editable inputs.
     */
    function storeOriginalValues() {
        originalValues.first_name = firstNameInput.value;
        originalValues.last_name = lastNameInput.value;
        originalValues.username = usernameInput.value;
    }

    /**
     * Restores the inputs to their previously stored original values.
     */
    function restoreOriginalValues() {
        firstNameInput.value = originalValues.first_name ?? ''; // Use nullish coalescing for safety
        lastNameInput.value = originalValues.last_name ?? '';
        usernameInput.value = originalValues.username ?? '';
    }

    /**
     * Sets the readonly state and corresponding styles for editable inputs.
     * @param {boolean} isReadonly - True to make fields readonly, false to make them editable.
     */
    function setReadonlyState(isReadonly) {
        editableInputs.forEach(input => {
            if (!input) return; // Skip if an input wasn't found
            input.readOnly = isReadonly;
            // Style toggling relies on HTML read-only: variants, no JS class changes needed here for input styling
        });
    }

    /**
     * Switches the UI to edit mode. Manages button visibility and display types.
     */
    function enterEditMode() {
        console.log("update_profile.js: enterEditMode() called.");
        storeOriginalValues();
        setReadonlyState(false); // Make fields editable

        // Hide Edit button
        editButton.classList.add('hidden');
        editButton.classList.remove('inline-flex'); // Remove its display type

        // Show Save button
        saveButton.classList.remove('hidden');
        saveButton.classList.add('inline-flex'); // Add its display type

        // Show Cancel button
        cancelButton.classList.remove('hidden');
        cancelButton.classList.add('inline-flex'); // Add its display type

        clearErrors(); // Clear any previous errors when starting edit
        // Try focusing the first editable field
        if (firstNameInput) {
             firstNameInput.focus();
             firstNameInput.select(); // Select text for easy replacement
        }
    }

    /**
     * Switches the UI back to view mode. Manages button visibility and display types.
     * @param {boolean} [revert=false] - If true, restores original values before exiting.
     */
    function exitEditMode(revert = false) {
         console.log("update_profile.js: exitEditMode() called. Revert:", revert);
        if (revert) {
            restoreOriginalValues();
        }
        setReadonlyState(true); // Make fields readonly again

        // Show Edit button
        editButton.classList.remove('hidden');
        editButton.classList.add('inline-flex'); // Add back its display type

        // Hide Save button
        saveButton.classList.add('hidden');
        saveButton.classList.remove('inline-flex'); // Remove its display type

        // Hide Cancel button
        cancelButton.classList.add('hidden');
        cancelButton.classList.remove('inline-flex'); // Remove its display type

        clearErrors(); // Clear errors when exiting mode

        // Reset save button state
        saveButton.disabled = false;
        saveButton.textContent = 'Save Changes';
    }

    // --- Initial Setup ---
    console.log("update_profile.js: Setting initial readonly state.");
    setReadonlyState(true); // Set initial state on page load

    // --- Event Listeners ---
    console.log("update_profile.js: Adding event listeners.");
    // Edit Button: Enter Edit Mode
    editButton.addEventListener('click', enterEditMode);

    // Cancel Button: Exit Edit Mode and Revert
    cancelButton.addEventListener('click', () => {
        exitEditMode(true); // Exit and revert changes
    });

    // Form Submission (Save Button is type="submit")
    profileForm.addEventListener('submit', async (event) => {
        event.preventDefault(); // Prevent default form submission
        clearErrors(); // Clear previous validation errors

        const formData = {
            first_name: firstNameInput.value.trim(),
            last_name: lastNameInput.value.trim(),
            username: usernameInput.value.trim() // Send empty string if blank
        };

        // Basic frontend validation
        let hasError = false;
        if (!formData.first_name) {
            showError('first_name', 'First name is required.');
            hasError = true;
        }
        if (!formData.last_name) {
            showError('last_name', 'Last name is required.');
            hasError = true;
        }
        if (hasError) {
             // Ensure showFlashMessage is available globally or imported
             if (typeof showFlashMessage === 'function') {
                 showFlashMessage("Please correct the errors below.", "warning");
             } else {
                 console.warn("showFlashMessage function not found.");
             }
             return; // Stay in edit mode
        }


        const originalButtonText = saveButton.textContent;
        saveButton.disabled = true;
        saveButton.textContent = 'Saving...';

        try {
            const response = await authFetch('/api/auth/profile/update', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                },
                body: JSON.stringify(formData)
            });

            // Handle cases where authFetch might intercept (e.g., redirect)
            if (!response) {
                console.warn("authFetch may have handled the request (e.g., redirect).");
                // Keep UI in saving state briefly or reset cautiously
                // It's safer to leave the button disabled until page potentially reloads
                return;
            }

            const data = await response.json(); // Assume JSON response even for errors

            if (response.ok) {
                 if (typeof showFlashMessage === 'function') {
                    showFlashMessage(data.message || 'Profile updated successfully!', 'success');
                 }
                // Update originalValues with the newly saved data BEFORE exiting edit mode
                storeOriginalValues();
                exitEditMode(false); // Exit edit mode, don't revert
            } else {
                // Handle validation errors (400) or other API errors (409, 500)
                if (response.status === 400 && data.details) {
                    displayValidationErrors(data.details);
                     if (typeof showFlashMessage === 'function') {
                        showFlashMessage(data.error || 'Please correct the errors below.', 'warning');
                     }
                } else {
                     if (typeof showFlashMessage === 'function') {
                        showFlashMessage(data.error || `Update failed (Status: ${response.status})`, 'error');
                     }
                }
                // Stay in edit mode and re-enable save button on failure
                saveButton.disabled = false;
                saveButton.textContent = originalButtonText;
            }

        } catch (error) {
            console.error('Error updating profile:', error);
             if (error.message && error.message.includes("Authentication required")) {
                 // Let authFetch handle redirect, maybe show a generic message
                  if (typeof showFlashMessage === 'function') {
                    showFlashMessage("Session expired. Please log in again.", "warning");
                  }
             } else {
                  if (typeof showFlashMessage === 'function') {
                    showFlashMessage('Network error or unexpected issue. Please try again.', 'error');
                  }
             }
             // Re-enable save button on failure
             saveButton.disabled = false;
             saveButton.textContent = originalButtonText;
        }
    });

}); // End DOMContentLoaded

// --- Helper Functions ---

/**
 * Displays validation errors returned from the API.
 * @param {object} errors - An object where keys are field names and values are error messages.
 */
function displayValidationErrors(errors) {
    // clearErrors(); // Usually called before this or at start of submit
    for (const field in errors) {
        // Ensure the field name matches an input ID if using showError directly
        showError(field, errors[field]);
    }
}

/**
 * Shows an error message for a specific field and applies error styling.
 * @param {string} field - The ID of the input field.
 * @param {string} message - The error message to display.
 */
function showError(field, message) {
    const errorElement = document.getElementById(`error-${field}`); // Assumes error element IDs follow pattern 'error-fieldId'
    const inputElement = document.getElementById(field);
    if (errorElement) {
        errorElement.textContent = message;
        // errorElement.classList.remove('hidden'); // If error elements are hidden by default
    }
    if (inputElement) {
        inputElement.classList.add('border-red-500'); // Add Tailwind error border class
        inputElement.setAttribute('aria-invalid', 'true');
        inputElement.setAttribute('aria-describedby', `error-${field}`); // Link input to error message
    }
}

/**
 * Clears all validation error messages and styling from the form.
 */
function clearErrors() {
    const errorElements = document.querySelectorAll('[id^="error-"]');
    errorElements.forEach(el => {
        el.textContent = '';
        // el.classList.add('hidden'); // If error elements are hidden by default
    });

    // Select only the inputs within the profile form that might have errors
    const inputElements = document.querySelectorAll('#update-profile-form input[type="text"], #update-profile-form input[type="password"]');
    inputElements.forEach(el => {
        el.classList.remove('border-red-500'); // Remove Tailwind error border class
        el.removeAttribute('aria-invalid');
        el.removeAttribute('aria-describedby'); // Remove link if error is cleared
    });
}