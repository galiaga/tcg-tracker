window.onload = function() {
    setInterval(autoRefreshAccessToken, 60000); 
    const token = localStorage.getItem("access_token");

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

function autoRefreshAccessToken() {
    const refreshToken = localStorage.getItem("refresh_token");
    const accessToken = localStorage.getItem("access_token");

    if (!refreshToken || !accessToken) {
        console.warn("Auto-refresh: tokens not found.");
        return;
    }

    try {
        const payload = JSON.parse(atob(accessToken.split(".")[1]));
        const expTime = payload.exp * 1000;
        const currentTime = Date.now();
        const timeUntilExpiration = expTime - currentTime;

        if (timeUntilExpiration < 120000) {
            console.log("Access token is about to expire. Refreshing...");

            fetch("/api/auth/refresh", {
                method: "POST",
                headers: {
                    "Authorization": `Bearer ${refreshToken}`,
                    "Content-Type": "application/json"
                }
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error("Refresh failed");
                }
                return response.json();
            })
            .then(data => {
                console.log("Access token refreshed successfully.");
                localStorage.setItem("access_token", data.access_token);
            })
            .catch(err => {
                console.error("Error refreshing token:", err);
                logout();
            });
        }
    } catch (err) {
        console.error("Failed to decode access token:", err);
        logout();
    }
}


async function authFetch(url, options = {}) {
    let token = localStorage.getItem("access_token");
    let refreshToken = localStorage.getItem("refresh_token");

    if (!token && window.location.pathname !== "/login") {
        console.warn("No access token found. Redirecting to login.");
        window.location.href = "/login";
        return null;
    } else if (!token && window.location.pathname === "/login") {
        return null;
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
            const newAccessToken = refreshData.access_token;

            if (!newAccessToken) {
                console.error("Refresh succeeded but no access token returned.");
                logout();
                return null;
            }

            localStorage.setItem("access_token", newAccessToken);
            console.log("New access token obtained:", newAccessToken);

            options.headers["Authorization"] = `Bearer ${newAccessToken}`;
            response = await fetch(url, options);
        } else {
            console.error("Refresh token invalid or expired.");
            logout();
            return null;
        }
    }

    return response;
}