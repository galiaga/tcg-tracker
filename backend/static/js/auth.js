window.onload = function() {
    const token = localStorage.getItem("access_token");

    console.log("Auth.js loaded. Token:", token);

    if (!token) {
        console.warn("No token found. Redirecting to login...");
        window.location.href = "/login";
        return;
    }

    try {
        const payload = JSON.parse(atob(token.split(".")[1])); 
        const expTime = payload.exp * 1000; 
        const currentTime = Date.now();

        if (expTime < currentTime) {
            console.warn("Token expired. Redirecting to login...");
            logout();
        }
    } catch (error) {
        console.error("Error decoding token:", error);
        logout();
    }
};

function logout() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    window.location.href = "/login";
}
