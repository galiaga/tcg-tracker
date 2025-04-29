// backend/static/js/auth/register.js

// --- Import Shared Utilities ---
import { validatePasswordComplexity } from '../utils/validation-utils.js';

// --- DOM Ready Event Listener ---
document.addEventListener("DOMContentLoaded", function () {
    const registerForm = document.getElementById("register-form");
    const passwordErrorDiv = document.getElementById("password-errors");

    if (registerForm && passwordErrorDiv) {
        // --- Form Submission Handler ---
        registerForm.addEventListener("submit", async function (event) {
            event.preventDefault();

            passwordErrorDiv.innerHTML = '';
            // clearFlashMessages(); // Assumes a function to clear general flash messages exists

            // --- Get Input Values ---
            const usernameInput = document.getElementById("username");
            const emailInput = document.getElementById("email");
            const passwordInput = document.getElementById("password");
            const confirmationInput = document.getElementById("confirmation");

            const username = usernameInput.value.trim();
            const email = emailInput.value.trim();
            const password = passwordInput.value;
            const confirmation = confirmationInput.value;

            // --- Frontend Validation (Basic Checks) ---
            if (!username || !email || !password || !confirmation) {
                 showFlashMessage("All fields (username, email, password, confirmation) are required.", "warning");
                 return;
            }
            if (password !== confirmation) {
                showFlashMessage("Passwords do not match.", "error");
                return;
            }

            // --- Frontend Validation (Password Complexity) ---
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
                    },
                    body: JSON.stringify({ username, email, password, confirmation }),
                });

                // --- Response Handling ---
                if (response.ok) {
                    const data = await response.json();
                    sessionStorage.setItem("flashMessage", `Welcome ${data.username || username}! Registration successful.`);
                    sessionStorage.setItem("flashType", "success");
                    window.location.href = "/login";
                } else {
                    let errorMessage = "Registration failed. Please try again.";
                    let messageType = "error";

                    if (response.status === 429) {
                        console.warn('Rate limit exceeded for registration');
                        errorMessage = 'Too many registration attempts. Please wait a while and try again.';
                        try {
                            const errorData = await response.json();
                            errorMessage = errorData.message || errorData.error || errorMessage;
                        } catch (e) { /* Ignore JSON parsing error */ }
                    } else {
                        try {
                            const errorData = await response.json();
                            errorMessage = errorData.error || `Registration failed (Status: ${response.status})`;

                            if (errorData.type === "VALIDATION_ERROR" && errorData.details && Array.isArray(errorData.details)) {
                                const errorList = document.createElement('ul');
                                errorList.className = 'list-disc list-inside text-red-600 text-sm mt-1';
                                errorData.details.forEach(errorText => {
                                    const listItem = document.createElement('li');
                                    listItem.textContent = errorText;
                                    errorList.appendChild(listItem);
                                });
                                passwordErrorDiv.appendChild(errorList);
                                errorMessage = "Please correct the password errors listed above.";
                            } else if (errorData.type === "DUPLICATE_USERNAME") {
                                console.warn("Duplicate username detected by backend");
                            } else if (errorData.type === "DUPLICATE_EMAIL") {
                                console.warn("Duplicate email detected by backend");
                            }

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