async function login() {
    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;

    try {
        const response = await fetch("/api/auth/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password })
        });

        const data = await response.json();

        if (response.ok) {
            localStorage.setItem("access_token", data.access_token);
            localStorage.setItem("refresh_token", data.refresh_token);
            localStorage.setItem("username", data.username);

            sessionStorage.setItem("flashMessage", `Welcome back, ${data.username}!`);
            sessionStorage.setItem("flashType", "success");

            console.log("Login successful, redirecting...");
            window.location.href = "/";
        } else {
            console.warn("Login failed. Clearing tokens.");
            localStorage.removeItem("access_token");
            localStorage.removeItem("refresh_token");

            showFlashMessage(data.error || "Login failed. Please try again.", "error");
        }
    } catch (error) {
        console.error("Error during login:", error);
        showFlashMessage("Network error. Please try again later.", "error");
    }
}
