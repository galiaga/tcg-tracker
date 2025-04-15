// CSRF Token Management
let csrfToken = null;

async function fetchAndStoreCSRFToken() {
    console.log("Attempting to fetch CSRF token...");
    try {
        // Assuming user is logged in if we attempt this
        const response = await fetch('/api/auth/csrf_token', {
            method: 'GET',
            credentials: 'include' // Ensure session cookie is sent
        });
        if (response.ok) {
            const data = await response.json();
            csrfToken = data.csrf_token;
            console.log("CSRF token fetched and stored:", csrfToken);
            return csrfToken;
        } else {
            console.error("Failed to fetch CSRF token:", response.status, response.statusText);
            // Maybe the session expired? Handle logout or error state
            if (response.status === 401) {
                 await handleLogout(true); // Force logout if session is gone
            }
            return null;
        }
    } catch (error) {
        console.error("Error fetching CSRF token:", error);
        return null;
    }
}

async function getCSRFToken() {
    // Return stored token if available, otherwise fetch it
    if (!csrfToken) {
        await fetchAndStoreCSRFToken();
    }
    return csrfToken;
}

// Main authentication fetch wrapper
export async function authFetch(url, options = {}) {
    options.headers = options.headers || {};
    if (options.body && !options.headers['Content-Type']) {
        options.headers['Content-Type'] = 'application/json';
    }
    options.credentials = 'include'; // Always send session cookie

    const method = options.method ? options.method.toUpperCase() : 'GET';

    // Add CSRF token header for state-changing methods
    // Adjust methods list if needed (e.g., add PATCH)
    const csrfMethods = ["POST", "PUT", "DELETE", "PATCH"];
    if (csrfMethods.includes(method)) {
        const token = await getCSRFToken(); // Fetch if not already stored
        if (token) {
            options.headers['X-CSRF-TOKEN'] = token; // Add the header
            console.log(`authFetch: Added X-CSRF-TOKEN header for ${method} ${url}`);
        } else {
            console.error(`authFetch: Could not get CSRF token for ${method} ${url}. Request may fail.`);
            // Optionally, you could prevent the fetch here if CSRF is absolutely required
            // return Promise.reject(new Error("CSRF token unavailable"));
        }
    }

    try {
        const response = await fetch(url, options);

        // Handle 401 Unauthorized (Session likely expired)
        if (response.status === 401) {
            console.warn(`authFetch: Received 401 Unauthorized for ${url}. Session likely expired.`);
            await handleLogout(true); // Force logout and redirect
            // Return a response that indicates failure, or throw an error
            // So calling code doesn't proceed as if successful.
            // Returning the original 401 response might be suitable sometimes.
             return response;
             // Or: throw new Error("Session expired");
        }

         // Handle 401 CSRF failure (if decorator sends 401 for CSRF)
        if (response.status === 401 && csrfMethods.includes(method)) {
             // Attempt to read error message if JSON
             try {
                 const errorData = await response.clone().json(); // Clone to read body safely
                 if (errorData.msg && errorData.msg.toLowerCase().includes("csrf")) {
                     console.error("authFetch: CSRF validation failed. Forcing logout.");
                     csrfToken = null; // Clear potentially stale token
                     await handleLogout(true);
                     return response; // Return the original response
                 }
             } catch(e) { /* Ignore if body isn't JSON */ }
             // If it was 401 but not CSRF, handle as generic session expiry above
        }


        // For other errors (403, 404, 500), let the caller handle them
        return response;

    } catch (error) {
        // Network errors
        console.error(`authFetch: Network or other error during fetch for ${url}:`, error);
        // Potentially check error type, maybe trigger logout if specific error occurs
        throw error; // Re-throw for the caller
    }
}

// Function to handle logout
export async function handleLogout(forceRedirect = false) {
    console.log(`handleLogout called. forceRedirect=${forceRedirect}`);
    csrfToken = null;
    try {
        const response = await fetch('/api/auth/logout', {
            method: 'POST',
            credentials: 'include', 
            headers: {
                'X-CSRF-TOKEN': await getCSRFToken() || ''
            }
        });
        if (!response.ok) {
            console.error('Logout API call failed:', response.status, response.statusText);
        } else {
            console.log("Logout API call successful, session cleared.");
        }
    } catch (error) {
        console.error('Error during logout fetch:', error);
    } finally {
        localStorage.removeItem('username'); 
        console.log("Redirecting to /login.");
        window.location.href = '/login'; 
    }
}


window.addEventListener('load', async function() {
    const logoutLink = document.querySelector('#nav-logout');
    if (logoutLink) {
        if (logoutLink.hasAttribute('onclick')) { logoutLink.removeAttribute('onclick'); }
        logoutLink.addEventListener('click', (event) => {
            event.preventDefault();
            handleLogout();
        });
        console.log("Attached logout handler to #nav-logout");
    }

    const mobileLogoutButton = document.querySelector('#mobile-navbar button[aria-label="Logout"]');
    if (mobileLogoutButton) {
        if (mobileLogoutButton.hasAttribute('onclick')) { mobileLogoutButton.removeAttribute('onclick'); }
        mobileLogoutButton.addEventListener('click', (event) => {
            event.preventDefault();
            handleLogout();
        });
        console.log("Attached logout handler to #mobile-navbar logout button");
    }

    if (window.location.pathname !== '/login' && window.location.pathname !== '/register') {
       await fetchAndStoreCSRFToken();
    } else {
        console.log("On login/register page, skipping initial CSRF fetch.");
    }

    console.log("Auth setup complete using Flask-Session.");

});

// Make functions globally available if needed
window.authFetch = authFetch;
window.handleLogout = handleLogout;