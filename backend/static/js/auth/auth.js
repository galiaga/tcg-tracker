let csrfToken = null;

async function fetchAndStoreCSRFToken() {
    try {
        const response = await fetch('/api/auth/csrf_token', {
            method: 'GET',
            credentials: 'include' // Ensure session cookie is sent
        });
        if (response.ok) {
            const data = await response.json();
            csrfToken = data.csrf_token;
            return csrfToken;
        } else {
            console.error("Failed to fetch CSRF token:", response.status, response.statusText);
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
    options.credentials = 'include'; 

    const method = options.method ? options.method.toUpperCase() : 'GET';

    const csrfMethods = ["POST", "PUT", "DELETE", "PATCH"];
    if (csrfMethods.includes(method)) {
        const token = await getCSRFToken(); 
        if (token) {
            options.headers['X-CSRF-TOKEN'] = token; 
        } else {
            console.error(`authFetch: Could not get CSRF token for ${method} ${url}. Request may fail.`);
        }
    }

    try {
        const response = await fetch(url, options);

        if (response.status === 401) {
            console.warn(`authFetch: Received 401 Unauthorized for ${url}. Session likely expired.`);
            await handleLogout(true);

             return response;
        }

        if (response.status === 401 && csrfMethods.includes(method)) {
             try {
                 const errorData = await response.clone().json(); 
                 if (errorData.msg && errorData.msg.toLowerCase().includes("csrf")) {
                     console.error("authFetch: CSRF validation failed. Forcing logout.");
                     csrfToken = null; 
                     await handleLogout(true);
                     return response; 
                 }
             } catch(e) { /* Ignore if body isn't JSON */ }
        }


        return response;

    } catch (error) {
        console.error(`authFetch: Network or other error during fetch for ${url}:`, error);
        throw error; 
    }
}

// Function to handle logout
export async function handleLogout(forceRedirect = false) {
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
        }
    } catch (error) {
        console.error('Error during logout fetch:', error);
    } finally {
        localStorage.removeItem('username'); 
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
    }

    const mobileLogoutButton = document.querySelector('#mobile-navbar button[aria-label="Logout"]');
    if (mobileLogoutButton) {
        if (mobileLogoutButton.hasAttribute('onclick')) { mobileLogoutButton.removeAttribute('onclick'); }
        mobileLogoutButton.addEventListener('click', (event) => {
            event.preventDefault();
            handleLogout();
        });
    }

    if (window.location.pathname !== '/login' && window.location.pathname !== '/register') {
       await fetchAndStoreCSRFToken();
    } else {
    }


});

// Make functions globally available if needed
window.authFetch = authFetch;
window.handleLogout = handleLogout;