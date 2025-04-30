// backend/static/js/auth/login.js

// Assuming showFlashMessage is globally available

async function handleLogin() {
    // Get email and password values
    const emailInput = document.getElementById("email");
    const passwordInput = document.getElementById("password");
    const email = emailInput?.value.trim(); // Use optional chaining and trim
    const password = passwordInput?.value;

    // Basic frontend check
    if (!email || !password) {
        showFlashMessage("Email and password are required.", "warning");
        return;
    }

    const loginForm = document.getElementById('login-form');
    const submitButton = loginForm?.querySelector('button[type="submit"]');
    const originalButtonText = submitButton?.textContent;

    // Disable button during request
    if(submitButton) {
        submitButton.disabled = true;
        submitButton.textContent = 'Signing in...';
    }

    try {
        const response = await fetch("/api/auth/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Accept": "application/json"
                // Include CSRF token if needed
                // 'X-CSRFToken': getCsrfToken()
             },
            // Send email instead of username
            body: JSON.stringify({ email, password })
        });

        if (response.ok) {
            const data = await response.json();
            const user = data.user; // Get user object from response

            // --- Store user info if needed, but rely on session cookie primarily ---
            // localStorage.setItem("userFirstName", user.first_name); // Example
            // localStorage.removeItem("username"); // Remove old username if stored

            // Log cookies after login for debugging
            console.log("All cookies after successful login:", document.cookie);

            // Use sessionStorage for success message on next page load
            // Use first name for greeting
            sessionStorage.setItem("flashMessage", `Welcome back, ${user.first_name}!`);
            sessionStorage.setItem("flashType", "success");

            console.log("Login successful, redirecting to dashboard...");
            window.location.href = "/my-decks"; // Redirect to main app page (e.g., decks)

        } else {
            // --- Handle non-OK responses (errors) ---
            let errorMessage = "Login failed. Please try again.";
            let messageType = "error";

            if (response.status === 429) {
                console.warn('Rate limit exceeded for login');
                errorMessage = 'Too many login attempts. Please wait a minute and try again.';
                try { const errorData = await response.json(); errorMessage = errorData.message || errorData.error || errorMessage; } catch (e) { /* Ignore */ }
            } else {
                 // Default error for 401 or other issues
                 errorMessage = 'Invalid email or password.';
                try {
                    const errorData = await response.json();
                    // Use backend error message if available, otherwise stick to default
                    errorMessage = errorData.error || errorMessage;
                } catch (e) {
                    console.warn("Could not parse error response JSON for status:", response.status);
                }
            }
            showFlashMessage(errorMessage, messageType);
        }
    } catch (error) {
        console.error("Network error during login:", error);
        showFlashMessage("Network error. Please check connection and try again.", "error");
    } finally {
        // Re-enable button
        if(submitButton) {
            submitButton.disabled = false;
            submitButton.textContent = originalButtonText;
        }
    }
}

// Add event listener when the DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', (event) => {
            event.preventDefault(); // Prevent default form submission
            handleLogin(); // Call the async login handler function
        });
    } else {
        console.warn("Login form with id 'login-form' not found.");
    }
});
