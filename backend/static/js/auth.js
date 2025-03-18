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

async function authFetch(url, options = {}) {
    let token = localStorage.getItem("access_token");
    let refreshToken = localStorage.getItem("refresh_token");

    // 🚨 NO redirigir si ya estamos en /login
    if (!token && window.location.pathname !== "/login") {
        console.warn("No access token found. Redirecting to login.");
        window.location.href = "/login";
        return null;
    } else if (!token && window.location.pathname === "/login") {
        return null;  // Si estamos en /login, no intentamos hacer la solicitud
    }

    options.headers = {
        ...options.headers,
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json"
    };

    let response = await fetch(url, options);

    if (response.status === 401 && refreshToken) {
        console.warn("Access token expired. Attempting refresh...");

        const refreshResponse = await fetch("/api/auth/refresh", {
            method: "POST",
            headers: {
                "Authorization": `Bearer ${refreshToken}`,
                "Content-Type": "application/json"
            }
        });

        if (refreshResponse.ok) {
            const refreshData = await refreshResponse.json();
            localStorage.setItem("access_token", refreshData.access_token);

            // Reintentar la solicitud con el nuevo token
            options.headers["Authorization"] = `Bearer ${refreshData.access_token}`;
            response = await fetch(url, options);
        } else {
            console.error("Refresh token expired. Logging out.");
            localStorage.removeItem("access_token");
            localStorage.removeItem("refresh_token");

            if (window.location.pathname !== "/login") {
                window.location.href = "/login";
            }
            return null;
        }
    }

    return response;
}
