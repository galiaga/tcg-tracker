async function login() {
    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;

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
            
            sessionStorage.setItem("flashMessage", `Welcome back, ${data.username}!`);
            sessionStorage.setItem("flashType", "success");

            console.log("Login successful, redirecting...");
            window.location.href = "/";
        } else {
            // Try to parse error message
            try {
                const errorData = await response.json();
                showFlashMessage(errorData.error || "Login failed. Please try again.", "error");
            } catch (e) {
                showFlashMessage("Login failed. Please try again.", "error");
            }
        }
    } catch (error) {
        console.error("Error during login:", error);
        showFlashMessage("Network error. Please try again later.", "error");
    }
}