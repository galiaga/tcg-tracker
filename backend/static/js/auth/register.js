// backend/static/js/auth/register.js

// --- Import Shared Utilities ---
import { validatePasswordComplexity } from '../utils/validation-utils.js';
// Assuming showFlashMessage is globally available (e.g., defined in flashMessages.js loaded in layout.html)
// If not, you might need to import it if it's modularized.

// --- DOM Ready Event Listener ---
document.addEventListener("DOMContentLoaded", function () {
    const registerForm = document.getElementById("register-form");
    const passwordErrorDiv = document.getElementById("password-errors");

    if (registerForm && passwordErrorDiv) {
        // --- Form Submission Handler ---
        registerForm.addEventListener("submit", async function (event) {
            event.preventDefault();

            passwordErrorDiv.innerHTML = '';
            // clearFlashMessages(); // Call your function to clear general flash messages if needed

            // --- Get Input Values ---
            const firstNameInput = document.getElementById("first_name"); // New
            const lastNameInput = document.getElementById("last_name");   // New
            const emailInput = document.getElementById("email");
            const passwordInput = document.getElementById("password");
            const confirmationInput = document.getElementById("confirmation");

            const firstName = firstNameInput.value.trim(); // New
            const lastName = lastNameInput.value.trim();   // New
            const email = emailInput.value.trim();
            const password = passwordInput.value;
            const confirmation = confirmationInput.value;

            // --- Frontend Validation (Basic Checks) ---
            // Updated required fields check
            if (!firstName || !lastName || !email || !password || !confirmation) {
                 showFlashMessage("All fields (first name, last name, email, password, confirmation) are required.", "warning");
                 return;
            }
            if (password !== confirmation) {
                showFlashMessage("Passwords do not match.", "error");
                return;
            }

            // --- Frontend Validation (Password Complexity) ---
            const complexityResult = validatePasswordComplexity(password);
            if (!complexityResult.isValid) {
                // (Keep existing password complexity display logic)
                const errorList = document.createElement('ul');
                errorList.className = 'space-y-1.5';
                complexityResult.errors.forEach(errorText => {
                    const listItem = document.createElement('li');
                    listItem.className = 'flex items-start text-sm';
                    const iconWrapper = document.createElement('span');
                    iconWrapper.className = 'flex-shrink-0 mr-1.5 mt-0.5 text-red-500';
                    iconWrapper.innerHTML = `
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4">
                          <path stroke-linecap="round" stroke-linejoin="round" d="M9.75 9.75l4.5 4.5m0-4.5l-4.5 4.5M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                    `;
                    const textSpan = document.createElement('span');
                    textSpan.className = 'text-red-600';
                    textSpan.textContent = errorText;
                    listItem.appendChild(iconWrapper);
                    listItem.appendChild(textSpan);
                    errorList.appendChild(listItem);
                });
                passwordErrorDiv.innerHTML = '';
                passwordErrorDiv.appendChild(errorList);
                return;
            } else {
                passwordErrorDiv.innerHTML = '';
            }

            // --- API Request ---
            const submitButton = registerForm.querySelector('button[type="submit"]');
            const originalButtonText = submitButton?.textContent;
            if(submitButton) {
                submitButton.disabled = true;
                submitButton.textContent = 'Registering...';
            }

            try {
                const response = await fetch("/api/auth/register", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "Accept": "application/json"
                        // Include CSRF token if your setup requires it for POST
                        // 'X-CSRFToken': getCsrfToken() // Assuming a function to get it
                    },
                    // Updated request body
                    body: JSON.stringify({
                        first_name: firstName, // Use snake_case for backend
                        last_name: lastName,   // Use snake_case for backend
                        email,
                        password,
                        confirmation
                        // No username sent here
                    }),
                });

                // --- Response Handling ---
                if (response.ok) {
                    const data = await response.json();
                    // Updated success message using first name from response
                    sessionStorage.setItem("flashMessage", `Welcome ${data.user?.first_name || firstName}! Registration successful.`);
                    sessionStorage.setItem("flashType", "success");
                    // Redirect to login or dashboard? Login seems appropriate after register.
                    window.location.href = "/login"; // Or use url_for('frontend.login_page') if passing via template
                } else {
                    // (Keep existing error handling logic, but remove username specific parts if any)
                    let errorMessage = "Registration failed. Please try again.";
                    let messageType = "error";

                    if (response.status === 429) {
                        console.warn('Rate limit exceeded for registration');
                        errorMessage = 'Too many registration attempts. Please wait a while and try again.';
                        try { const errorData = await response.json(); errorMessage = errorData.message || errorData.error || errorMessage; } catch (e) { /* Ignore */ }
                    } else {
                        try {
                            const errorData = await response.json();
                            errorMessage = errorData.error || `Registration failed (Status: ${response.status})`;

                            if (errorData.type === "VALIDATION_ERROR" && errorData.details && Array.isArray(errorData.details)) {
                                // (Keep password error display logic)
                                const errorList = document.createElement('ul');
                                errorList.className = 'list-disc list-inside text-red-600 text-sm mt-1'; // Adjust styling if needed
                                errorData.details.forEach(errorText => {
                                    const listItem = document.createElement('li');
                                    listItem.textContent = errorText;
                                    errorList.appendChild(listItem);
                                });
                                passwordErrorDiv.appendChild(errorList);
                                errorMessage = "Please correct the password errors listed above.";
                            } else if (errorData.type === "DUPLICATE_EMAIL") {
                                console.warn("Duplicate email detected by backend");
                                // You might want to highlight the email field or show a specific message
                            }
                            // No need to specifically handle DUPLICATE_USERNAME here anymore

                        } catch (e) {
                            errorMessage = `Registration failed (Status: ${response.status})`;
                            console.warn("Could not parse error response JSON for status:", response.status);
                        }
                    }
                    showFlashMessage(errorMessage, messageType);
                }
            } catch (error) {
                console.error("Network error during registration:", error);
                showFlashMessage("Network error. Please check connection and try again.", "error");
            } finally {
                 // --- Final Cleanup ---
                 if(submitButton) {
                    submitButton.disabled = false;
                    submitButton.textContent = originalButtonText;
                }
            }
        });
    } else {
        if (!registerForm) console.warn("Register form not found on this page.");
        if (!passwordErrorDiv) console.warn("Password error display div (#password-errors) not found on this page.");
    }
});