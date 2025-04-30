// backend/static/js/profile/change_password.js

import { authFetch } from '../auth/auth.js'; // Assuming authFetch handles CSRF etc.
import { validatePasswordComplexity } from '../utils/validation-utils.js'; // Reuse complexity checker

// Assuming showFlashMessage is globally available

document.addEventListener('DOMContentLoaded', () => {
    const changePasswordForm = document.getElementById('change-password-form');
    const newPasswordErrorDiv = document.getElementById('new-password-errors'); // Div for complexity errors

    if (changePasswordForm && newPasswordErrorDiv) {
        changePasswordForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            clearChangePasswordErrors(); // Clear previous errors

            const currentPasswordInput = document.getElementById('current_password');
            const newPasswordInput = document.getElementById('new_password');
            const confirmPasswordInput = document.getElementById('confirm_new_password');
            const submitButton = changePasswordForm.querySelector('button[type="submit"]');
            const originalButtonText = submitButton.textContent;

            const currentPassword = currentPasswordInput.value;
            const newPassword = newPasswordInput.value;
            const confirmation = confirmPasswordInput.value;

            // --- Frontend Validation ---
            let hasFrontendErrors = false;
            if (!currentPassword) {
                showChangePasswordError('current_password', 'Current password is required.');
                hasFrontendErrors = true;
            }
            if (!newPassword) {
                // Show error near input, but complexity check below handles detailed message
                showChangePasswordError('new_password', 'New password is required.');
                hasFrontendErrors = true;
            }
            if (!confirmation) {
                showChangePasswordError('confirm_new_password', 'Confirmation password is required.');
                hasFrontendErrors = true;
            }
            // Only check match if both fields have values (avoid redundant errors)
            if (newPassword && confirmation && newPassword !== confirmation) {
                showChangePasswordError('confirm_new_password', 'New passwords do not match.');
                hasFrontendErrors = true;
            }

            // Frontend Complexity Check (only if new password provided)
            if (newPassword) {
                const complexityResult = validatePasswordComplexity(newPassword);
                if (!complexityResult.isValid) {
                    displayPasswordComplexityErrors(complexityResult.errors);
                    // Mark the new_password field as invalid visually
                    showChangePasswordError('new_password', ''); // Add red border without text msg
                    hasFrontendErrors = true;
                }
            }

            if (hasFrontendErrors) {
                return; // Stop if frontend validation fails
            }

            // --- API Request ---
            submitButton.disabled = true;
            submitButton.textContent = 'Changing...';

            try {
                const response = await authFetch('/api/auth/profile/change-password', {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json',
                    },
                    body: JSON.stringify({
                        current_password: currentPassword,
                        new_password: newPassword,
                        confirmation: confirmation
                    })
                });

                 if (!response) { // Handle case where authFetch handled redirect (e.g., 401)
                     console.warn("authFetch returned no response, likely handled auth redirect.");
                     if(submitButton) { submitButton.disabled = false; submitButton.textContent = originalButtonText; }
                     return;
                 }

                // Try parsing JSON always, default to empty object on failure
                const data = await response.json().catch(() => ({}));

                if (response.ok) { // Status 200-299
                    showFlashMessage(data.message || 'Password changed successfully!', 'success');
                    // Clear the form fields on success
                    currentPasswordInput.value = '';
                    newPasswordInput.value = '';
                    confirmPasswordInput.value = '';
                } else {
                    // --- Handle Specific Error Statuses/Types ---
                    let errorMessage = data.error || data.message || `Request failed (Status: ${response.status})`;
                    let messageType = "error"; // Default to error

                    if (response.status === 429) {
                        console.warn('Rate limit exceeded for password change.');
                        errorMessage = data.message || "Too many attempts. Please wait before trying again.";
                        messageType = "warning";
                    } else if (response.status === 400) {
                        messageType = "warning"; // Use warning for validation errors
                        if (data.type === 'INVALID_CURRENT_PASSWORD') {
                            showChangePasswordError('current_password', data.error || 'Incorrect current password.');
                            errorMessage = "Incorrect current password provided."; // More direct flash message
                        } else if (data.type === 'PASSWORD_MISMATCH') {
                            showChangePasswordError('confirm_new_password', data.error || 'New passwords do not match.');
                             errorMessage = "New passwords do not match.";
                        } else if (data.type === 'WEAK_PASSWORD' && data.details) {
                            displayPasswordComplexityErrors(data.details);
                            showChangePasswordError('new_password', ''); // Add red border
                            errorMessage = data.error || 'Password does not meet requirements.';
                        } else if (data.type === 'PASSWORD_SAME_AS_OLD') {
                            showChangePasswordError('new_password', data.error || 'New password cannot be the same as the old one.');
                             errorMessage = data.error || 'New password cannot be the same as the current one.';
                        } else {
                            // Generic 400 (e.g., missing fields if somehow bypassed frontend check)
                            errorMessage = data.error || 'Failed to change password. Please check inputs.';
                        }
                    } else {
                        // Handle other non-OK statuses (401, 403, 404, 500 etc.)
                         console.error(`Password change failed with status ${response.status}:`, data);
                         errorMessage = data.error || data.message || `An unexpected error occurred (Status: ${response.status})`;
                    }
                    showFlashMessage(errorMessage, messageType);
                    // --- End Specific Error Handling ---
                }

            } catch (error) {
                console.error('Error changing password:', error);
                 if (error.message && error.message.includes("Authentication required")) {
                     // Let authFetch handle redirect
                     showFlashMessage("Session expired. Please log in again.", "warning");
                 } else {
                     showFlashMessage('Network error. Please try again.', 'error');
                 }
            } finally {
                submitButton.disabled = false;
                submitButton.textContent = originalButtonText;
            }
        });
    } else {
         if (!changePasswordForm) console.warn("Change password form not found.");
         if (!newPasswordErrorDiv) console.warn("New password error div not found.");
    }
});

// --- Helper Functions for Change Password Form ---

function displayPasswordComplexityErrors(errors) {
    const passwordErrorDiv = document.getElementById('new-password-errors');
    if (!passwordErrorDiv) return;

    const errorList = document.createElement('ul');
    errorList.className = 'space-y-1.5'; // Use similar styling as registration
    errors.forEach(errorText => {
        const listItem = document.createElement('li');
        listItem.className = 'flex items-start text-sm';
        const iconWrapper = document.createElement('span');
        // Use warning color like orange/yellow for complexity issues
        iconWrapper.className = 'flex-shrink-0 mr-1.5 mt-0.5 text-orange-500';
        iconWrapper.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
            </svg>
        `;
        const textSpan = document.createElement('span');
        // Use a slightly less harsh color for complexity text
        textSpan.className = 'text-orange-700';
        textSpan.textContent = errorText;
        listItem.appendChild(iconWrapper);
        listItem.appendChild(textSpan);
        errorList.appendChild(listItem);
    });
    passwordErrorDiv.innerHTML = ''; // Clear previous
    passwordErrorDiv.appendChild(errorList);
}


function showChangePasswordError(fieldId, message) {
    const errorElement = document.getElementById(`error-${fieldId}`); // Assumes error p tags have id="error-fieldId"
    const inputElement = document.getElementById(fieldId);
    if (errorElement && message) { // Only show text if message is provided
        errorElement.textContent = message;
    }
    if (inputElement) {
        inputElement.classList.add('border-red-500'); // Always add red border for error state
        inputElement.setAttribute('aria-invalid', 'true');
    }
}

function clearChangePasswordErrors() {
    const form = document.getElementById('change-password-form');
    if (!form) return;
    // Clear specific field errors
    const errorElements = form.querySelectorAll('[id^="error-"]');
    errorElements.forEach(el => el.textContent = '');
    // Clear complexity errors
    const complexityDiv = document.getElementById('new-password-errors');
    if (complexityDiv) complexityDiv.innerHTML = '';
    // Clear input styles
    const inputElements = form.querySelectorAll('input[type="password"]');
    inputElements.forEach(el => {
        el.classList.remove('border-red-500');
        el.removeAttribute('aria-invalid');
    });
}