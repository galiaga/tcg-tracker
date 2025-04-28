// backend/static/js/auth/forgot-password.js

document.addEventListener("DOMContentLoaded", function () {
    const forgotPasswordForm = document.getElementById("forgot-password-form");

    if (forgotPasswordForm) {
        forgotPasswordForm.addEventListener("submit", async function (event) {
            event.preventDefault();

            const emailInput = document.getElementById("email");
            const email = emailInput.value.trim();

            if (!email) {
                showFlashMessage("Please enter your email address.", "warning");
                return;
            }

            // Optional: Basic frontend email format check (though backend validates too)
            // const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            // if (!emailRegex.test(email)) {
            //     showFlashMessage("Please enter a valid email address format.", "warning");
            //     return;
            // }

            // Display loading state maybe? (Optional)
            const submitButton = forgotPasswordForm.querySelector('button[type="submit"]');
            const originalButtonText = submitButton.textContent;
            submitButton.disabled = true;
            submitButton.textContent = 'Sending...';


            try {
                const response = await fetch("/api/auth/forgot-password", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "Accept": "application/json"
                        // Add CSRF token if required by your setup for this endpoint
                    },
                    body: JSON.stringify({ email: email }),
                });

                // Backend always returns 200 OK with a generic message
                // So we just need to display that message
                const data = await response.json(); // Get the generic message
                showFlashMessage(data.message || "Request processed. If your email is registered, you'll receive a reset link.", "info"); // Use 'info' or 'success' type

                // Optionally clear the form or redirect, but often just showing the message is enough
                emailInput.value = ''; // Clear field after successful request


            } catch (error) {
                console.error("Network error during forgot password request:", error);
                showFlashMessage("Network error. Please check connection and try again.", "error");
            } finally {
                 // Restore button state
                 submitButton.disabled = false;
                 submitButton.textContent = originalButtonText;
            }
        });
    } else {
        console.warn("Forgot password form not found on this page.");
    }
});

// Ensure showFlashMessage function is available
// function showFlashMessage(message, type) { /* ... */ }