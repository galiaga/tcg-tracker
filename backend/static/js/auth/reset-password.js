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
                errorList.className = 'list-disc list-inside text-red-600';
                complexityResult.errors.forEach(errorText => {
                    const listItem = document.createElement('li');
                    listItem.textContent = errorText;
                    errorList.appendChild(listItem);
                });
                passwordErrorDiv.appendChild(errorList);
                return;
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