// backend/static/js/auth/reset-password.js

// --- Import Shared Utilities ---
import { validatePasswordComplexity } from '../utils/validation-utils.js';

// --- DOM Ready Event Listener ---
document.addEventListener("DOMContentLoaded", function () {
    const resetPasswordForm = document.getElementById("reset-password-form");
    const passwordErrorDiv = document.getElementById("password-errors");

    if (resetPasswordForm && passwordErrorDiv) {
        // --- Form Submission Handler ---
        resetPasswordForm.addEventListener("submit", async function (event) {
            event.preventDefault();

            passwordErrorDiv.innerHTML = '';

            // --- Get Input Values and Token ---
            const passwordInput = document.getElementById("password");
            const confirmationInput = document.getElementById("confirmation");
            const password = passwordInput.value;
            const confirmation = confirmationInput.value;

            const pathSegments = window.location.pathname.split('/');
            const token = pathSegments[pathSegments.length - 1];

            if (!token) {
                console.error("Reset token not found in URL path.");
                showFlashMessage("Invalid reset link. Token missing.", "error");
                return;
            }

            // --- Frontend Validation ---
            if (!password || !confirmation) {
                showFlashMessage("Please enter and confirm your new password.", "warning");
                return;
            }
            if (password !== confirmation) {
                showFlashMessage("Passwords do not match.", "error");
                return;
            }

            const complexityResult = validatePasswordComplexity(password);
            if (!complexityResult.isValid) {
                const errorList = document.createElement('ul');
                // Remove list-disc/list-inside, add spacing between items
                errorList.className = 'space-y-1.5'; // Adjust spacing as needed (e.g., space-y-1, space-y-2)
            
                complexityResult.errors.forEach(errorText => {
                    const listItem = document.createElement('li');
                    // Use flexbox to align icon and text
                    listItem.className = 'flex items-start text-sm'; 
            
                    // Create the icon wrapper (adjust color and size here)
                    const iconWrapper = document.createElement('span');
                    iconWrapper.className = 'flex-shrink-0 mr-1.5 mt-0.5'; 
            
                    // --- Icon Color Choice ---
                    iconWrapper.classList.add('text-red-500');
            
                    iconWrapper.innerHTML = `
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4">
                          <path stroke-linecap="round" stroke-linejoin="round" d="M9.75 9.75l4.5 4.5m0-4.5l-4.5 4.5M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                    `; 
            
                    // Create the text span (use a softer red or keep the original red)
                    const textSpan = document.createElement('span');
                    textSpan.className = 'text-red-600';
                    textSpan.textContent = errorText;
            
                    // Append icon and text to the list item
                    listItem.appendChild(iconWrapper);
                    listItem.appendChild(textSpan);
            
                    // Append the list item to the list
                    errorList.appendChild(listItem);
                });
            
                // Clear previous errors and append the new list
                passwordErrorDiv.innerHTML = ''; // Clear previous content
                passwordErrorDiv.appendChild(errorList);
                return;
            } else {
                // Clear errors if valid
                passwordErrorDiv.innerHTML = '';
            }

            // --- API Request ---
            const submitButton = resetPasswordForm.querySelector('button[type="submit"]');
            const originalButtonText = submitButton.textContent;
            submitButton.disabled = true;
            submitButton.textContent = 'Resetting...';

            try {
                const apiUrl = `/api/auth/reset-password/${token}`;
                const response = await fetch(apiUrl, {
                    method: 'POST', // Specify POST method
                    headers: {
                        'Content-Type': 'application/json',
                        // No CSRF token needed here usually, as it's unauthenticated
                        // and relies on the itsdangerous token for security.
                    },
                    body: JSON.stringify({ password: password }) // Send password in body
                });

                // --- Response Handling ---
                if (response.ok) {
                    const data = await response.json();
                    sessionStorage.setItem("flashMessage", data.message || "Password successfully updated! Please log in.");
                    sessionStorage.setItem("flashType", "success");
                    window.location.href = "/login";
                } else {
                    let errorMessage = "Failed to reset password. Please try again.";
                    let messageType = "error";
                    try {
                        const errorData = await response.json();
                        errorMessage = errorData.error || `Error: ${response.status}`;
                        if (errorData.type === "TOKEN_EXPIRED") { errorMessage = "Your password reset link has expired. Please request a new one."; }
                        else if (errorData.type === "TOKEN_INVALID" || errorData.type === "TOKEN_ERROR") { errorMessage = "This password reset link is invalid or corrupted. Please request a new one."; }
                        else if (errorData.type === "USER_NOT_FOUND") { errorMessage = "Could not find user associated with this reset request."; }
                        else if (errorData.type === "DB_ERROR" || errorData.type === "CONFIG_ERROR") { errorMessage = "A server error occurred. Please try again later."; }
                    } catch (e) {
                        errorMessage = `Password reset failed (Status: ${response.status})`;
                    }
                    showFlashMessage(errorMessage, messageType);
                }

            } catch (error) {
                console.error("Network error during password reset:", error);
                showFlashMessage("Network error. Please check connection and try again.", "error");
            } finally {
                // --- Final Cleanup ---
                submitButton.disabled = false;
                submitButton.textContent = originalButtonText;
            }
        });
    } else {
        if (!resetPasswordForm) console.warn("Reset password form not found on this page.");
        if (!passwordErrorDiv) console.warn("Password error display div not found on this page.");
    }
});