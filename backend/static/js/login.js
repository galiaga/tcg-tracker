async function login() {
    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;

    // Assuming your original working code used showFlashMessage like this
    // Make sure showFlashMessage is defined and accessible
    // function showFlashMessage(message, type) { ... implementation ... }

    try {
        const response = await fetch("/api/auth/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: 'include', // Critical for cookie storage
            body: JSON.stringify({ username, password })
        });

        // Check if login was successful
        if (response.ok) {
            const data = await response.json();

            // Just store username, don't try to store tokens
            localStorage.setItem("username", data.username);

            // Log cookies after login for debugging
            console.log("All cookies after login:", document.cookie);

            // Use sessionStorage for success message on next page load
            sessionStorage.setItem("flashMessage", `Welcome back, ${data.username}!`);
            sessionStorage.setItem("flashType", "success");

            console.log("Login successful, redirecting...");
            window.location.href = "/";

        } else {
            // --- MODIFICATION START ---
            // Handle non-OK responses (errors)

            let errorMessage = "Login failed. Please try again."; // Default error message
            let messageType = "error"; // Default message type

            // Check specifically for Rate Limit Exceeded status
            if (response.status === 429) {
                console.warn('Rate limit exceeded for login');
                errorMessage = 'Too many login attempts. Please wait a minute and try again.';
                // Try to get a more specific message from the 429 response body if available
                try {
                    const errorData = await response.json();
                    errorMessage = errorData.message || errorData.error || errorMessage;
                } catch (e) { /* Ignore if 429 response body isn't JSON */ }

            } else {
                // Original logic for other errors (401, 400, 500 etc.)
                if (response.status === 401) {
                     errorMessage = 'Invalid username or password.'; // Specific default for 401
                }
                // Try to parse error message from the JSON body for any error
                try {
                    const errorData = await response.json();
                    errorMessage = errorData.error || errorMessage; // Prefer backend error message
                } catch (e) {
                    // Keep the errorMessage determined by status code if JSON parsing fails
                    console.warn("Could not parse error response JSON for status:", response.status);
                }
            }

            // Call the function that displayed the messages correctly in your original version
            showFlashMessage(errorMessage, messageType);
            // --- MODIFICATION END ---
        }
    } catch (error) {
        // Original network error handling
        console.error("Error during login:", error);
        showFlashMessage("Network error. Please try again later.", "error");
    }
}

// Make sure the login function is attached to the form submit event
// (Keep the DOMContentLoaded listener from previous examples if needed)
document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('login-form'); // Assuming your form has id="login-form"
    if (loginForm) {
        loginForm.addEventListener('submit', (event) => {
            event.preventDefault(); // Prevent default form submission
            login(); // Call the async login function
        });
    }
});

// Ensure the showFlashMessage function used by your original working code is defined and accessible here.
// For example:
// function showFlashMessage(message, type) {
//    console.log(`Flash (${type}): ${message}`);
//    // ... The rest of your original implementation that showed the styled banner ...
// }