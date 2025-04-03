window.onload = function() {
    setInterval(autoRefreshAccessToken, 60 * 1000);
    const token = localStorage.getItem("access_token");
    const isAuthPage = window.location.pathname.endsWith('/login') || window.location.pathname.endsWith('/register');

    if (!token) {
        if (!isAuthPage) {
            console.warn("No token found. Redirecting to login...");
            window.location.href = "/login";
        }
        return;
    }

    try {
        const payload = JSON.parse(atob(token.split(".")[1]));
        const expTime = payload.exp * 1000;
        const currentTime = Date.now();

        if (expTime < currentTime) {
            console.warn("Token expired.");
            if (!isAuthPage) {
                 console.log("Logging out due to expired token on non-auth page.");
                 logout();
            } else {
                 console.log("Expired token found on auth page, clearing tokens but staying.");
                 localStorage.removeItem("access_token");
                 localStorage.removeItem("refresh_token");
            }
        }
    } catch (error) {
        console.error("Error decoding token:", error);
        if (!isAuthPage) {
            console.log("Logging out due to invalid token on non-auth page.");
            logout();
        } else {
             console.log("Invalid token found on auth page, clearing tokens but staying.");
             localStorage.removeItem("access_token");
             localStorage.removeItem("refresh_token");
        }
    }
};

export function logout() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    if (!window.location.pathname.endsWith('/login')) {
        window.location.href = "/login";
    } else {

    }
}

function autoRefreshAccessToken() {
    const refreshToken = localStorage.getItem("refresh_token");
    const accessToken = localStorage.getItem("access_token");

    if (!refreshToken || !accessToken) {
        return;
    }

    try {
        const payload = JSON.parse(atob(accessToken.split(".")[1]));
        const expTime = payload.exp * 1000;
        const currentTime = Date.now();
        const timeUntilExpiration = expTime - currentTime;
        const refreshThreshold = 2 * 60 * 1000;

        if (timeUntilExpiration < refreshThreshold) {
            console.log("Attempting token auto-refresh...");

            fetch("/api/auth/refresh", {
                method: "POST",
                headers: {
                    "Authorization": `Bearer ${refreshToken}`,
                    "Content-Type": "application/json"
                }
            })
            .then(response => {
                if (!response.ok) {
                     return response.json().then(errData => {
                         throw new Error(errData.message || `Refresh failed with status ${response.status}`);
                     }).catch(() => {
                          throw new Error(`Refresh failed with status ${response.status}`);
                     });
                }
                return response.json();
            })
            .then(data => {
                if (data.access_token) {
                    localStorage.setItem("access_token", data.access_token);
                    console.log("Access token refreshed via auto-refresh.");
                } else {
                     console.warn("Refresh response missing access token.");
                     logout();
                }
            })
            .catch(err => {
                console.error("Error during token auto-refresh:", err.message);
                logout();
            });
        }
    } catch (err) {
        console.error("Failed to decode access token during auto-refresh check:", err);
        logout();
    }
}

export async function authFetch(url, options = {}) {
    let token = localStorage.getItem("access_token");
    const refreshToken = localStorage.getItem("refresh_token");
    const isAuthPage = window.location.pathname.endsWith('/login') || window.location.pathname.endsWith('/register');

    if (!token) {
        if (!isAuthPage) {
            console.warn("authFetch: No access token. Logging out.");
            logout();
            return Promise.reject(new Error("No access token"));
        } else {
            options.headers = { ...options.headers };
            delete options.headers["Authorization"];
            options.headers["Content-Type"] = options.headers["Content-Type"] || "application/json";
        }
    } else {
        options.headers = {
            ...options.headers,
            "Authorization": `Bearer ${token}`,
            "Content-Type": options.headers?.["Content-Type"] || "application/json"
        };
    }

    try {
        let response = await fetch(url, options);

        if (response.status === 401 && refreshToken && token) {
            console.warn("authFetch: 401 Unauthorized. Attempting token refresh...");
            try {
                const refreshResponse = await fetch("/api/auth/refresh", {
                    method: "POST",
                    headers: {
                        "Authorization": `Bearer ${refreshToken}`,
                        "Content-Type": "application/json"
                    }
                });
                 const refreshData = await refreshResponse.json();

                if (refreshResponse.ok && refreshData.access_token) {
                    console.log("authFetch: Token refreshed successfully.");
                    localStorage.setItem("access_token", refreshData.access_token);
                    options.headers["Authorization"] = `Bearer ${refreshData.access_token}`;
                    response = await fetch(url, options);
                } else {
                    console.error("authFetch: Refresh token failed or returned invalid data.");
                    logout();
                    return Promise.reject(new Error(refreshData.message || "Token refresh failed"));
                }
            } catch (refreshError) {
                 console.error("authFetch: Exception during token refresh:", refreshError);
                 logout();
                 return Promise.reject(refreshError);
            }
        }
        return response;
    } catch (error) {
        console.error(`authFetch: Fetch error for ${url}:`, error);
        throw error;
    }
}

window.logout = logout;