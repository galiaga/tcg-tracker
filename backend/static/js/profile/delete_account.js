// backend/static/js/profile/delete_account.js

import { authFetch } from '../auth/auth.js'; // Assuming authFetch handles CSRF etc.
// Assuming showFlashMessage is globally available

document.addEventListener('DOMContentLoaded', () => {
    // --- Modal Elements ---
    const modal = document.getElementById('delete-account-modal');
    const openModalButton = document.getElementById('open-delete-modal-button');
    const closeModalButton = document.getElementById('cancel-delete-button');
    const confirmDeleteButton = document.getElementById('confirm-delete-button');
    const modalOverlay = document.getElementById('delete-modal-overlay');
    const passwordInput = document.getElementById('delete-confirm-password');
    const confirmTextInput = document.getElementById('delete-confirm-text');
    const passwordErrorEl = document.getElementById('error-delete-confirm-password');

    // --- Event Listeners ---
    if (openModalButton && modal) {
        openModalButton.addEventListener('click', openModal);
    }
    if (closeModalButton && modal) {
        closeModalButton.addEventListener('click', closeModal);
    }
    if (modalOverlay && modal) {
        modalOverlay.addEventListener('click', closeModal); // Close on overlay click
    }
    if (confirmDeleteButton && modal) {
        confirmDeleteButton.addEventListener('click', handleDeleteConfirm);
    }
    // Add listeners to enable/disable confirm button based on input
    if (passwordInput && confirmTextInput && confirmDeleteButton) {
        passwordInput.addEventListener('input', validateModalInputs);
        confirmTextInput.addEventListener('input', validateModalInputs);
    }


    // --- Modal Functions ---
    function openModal() {
        if (modal) {
            modal.classList.remove('hidden');
            // Reset form state when opening
            if (passwordInput) passwordInput.value = '';
            if (confirmTextInput) confirmTextInput.value = '';
            if (passwordErrorEl) passwordErrorEl.textContent = '';
            if (confirmDeleteButton) confirmDeleteButton.disabled = true;
            // Focus the password input when modal opens
            setTimeout(() => passwordInput?.focus(), 50);
        }
    }

    function closeModal() {
        if (modal) {
            modal.classList.add('hidden');
        }
    }

    function validateModalInputs() {
        const passwordFilled = passwordInput && passwordInput.value.trim() !== '';
        const textMatches = confirmTextInput && confirmTextInput.value.trim().toUpperCase() === 'DELETE';
        if (confirmDeleteButton) {
            confirmDeleteButton.disabled = !(passwordFilled && textMatches);
        }
    }

    async function handleDeleteConfirm() {
        if (!passwordInput || !confirmTextInput || !confirmDeleteButton) return;

        const password = passwordInput.value; // Don't trim password
        const confirmationText = confirmTextInput.value.trim().toUpperCase();

        // Final check (should be redundant due to button state, but safe)
        if (!password || confirmationText !== 'DELETE') {
            showFlashMessage("Please enter your password and type 'DELETE' to confirm.", "warning");
            return;
        }

        // Disable button during request
        confirmDeleteButton.disabled = true;
        const originalButtonText = confirmDeleteButton.textContent;
        confirmDeleteButton.textContent = 'Deleting...';
        if (passwordErrorEl) passwordErrorEl.textContent = ''; // Clear previous password error

        try {
            const response = await authFetch('/api/auth/profile/delete', {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                },
                body: JSON.stringify({ password: password }) // Send current password
            });

             if (!response) { // authFetch handled redirect (e.g., 401)
                 console.warn("authFetch returned no response during delete, likely handled auth redirect.");
                 // Button state might be stuck, reset manually if needed after potential redirect
                 return;
             }

            const data = await response.json().catch(() => ({})); // Attempt to parse JSON

            if (response.ok) { // Status 200-299
                console.log("Account deletion successful.");
                // Set flash message for login page
                sessionStorage.setItem("flashMessage", data.message || "Your account has been deactivated.");
                sessionStorage.setItem("flashType", "success");
                // Redirect to login page (backend should have cleared session)
                window.location.href = '/login'; // Adjust if needed
            } else {
                // Handle errors (e.g., incorrect password - 403)
                let errorMessage = data.error || `Deletion failed (Status: ${response.status})`;
                if (response.status === 403 && data.type === 'INVALID_PASSWORD') {
                    if (passwordErrorEl) passwordErrorEl.textContent = data.error || 'Incorrect password.';
                    errorMessage = 'Incorrect password provided.'; // More concise flash message
                } else {
                    console.error(`Account deletion failed with status ${response.status}:`, data);
                }
                showFlashMessage(errorMessage, 'error');
                // Re-enable button on failure
                confirmDeleteButton.disabled = false;
                confirmDeleteButton.textContent = originalButtonText;
                validateModalInputs(); // Re-check if button should be enabled
            }

        } catch (error) {
            console.error('Error deleting account:', error);
            showFlashMessage('Network error or unexpected issue during account deletion.', 'error');
            // Re-enable button on failure
            confirmDeleteButton.disabled = false;
            confirmDeleteButton.textContent = originalButtonText;
            validateModalInputs(); // Re-check if button should be enabled
        }
    }

});