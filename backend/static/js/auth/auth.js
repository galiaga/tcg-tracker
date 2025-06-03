// backend/static/js/auth/auth.js

// --- CSRF Token Handling ---

let csrfToken = null;

async function fetchAndStoreCSRFToken() {
    if (csrfToken) {
        return csrfToken;
    }
    try {
        const response = await fetch('/api/auth/csrf_token', {
            method: 'GET',
            credentials: 'include'
        });
        if (response.ok) {
            const data = await response.json();
            csrfToken = data.csrf_token;
            return csrfToken;
        } else {
            if (response.status === 401) {
            } else {
                 console.error("fetchAndStoreCSRFToken: Failed to fetch CSRF token:", response.status, response.statusText);
            }
            csrfToken = null;
            return null;
        }
    } catch (error) {
        console.error("fetchAndStoreCSRFToken: Network error fetching CSRF token:", error);
        csrfToken = null;
        return null;
    }
}

async function getCSRFToken() {
    if (!csrfToken) {
        await fetchAndStoreCSRFToken();
    }
    return csrfToken;
}

// --- Authenticated Fetch Wrapper ---

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
            console.warn(`authFetch: CSRF token not available for ${method} ${url}. User might not be logged in.`);
        }
    }

    try {
        const response = await fetch(url, options);

        if (response.status === 401) {
            console.warn(`authFetch: Received 401 Unauthorized for ${url}. Session likely expired. Forcing logout.`);
            await handleLogout();
            return response;
        }

        return response;

    } catch (error) {
        console.error(`authFetch: Network or other error during fetch for ${url}:`, error);
        throw error;
    }
}

// --- Logout Handler ---

export async function handleLogout() {
    const token = await getCSRFToken();
    csrfToken = null;

    try {
        const response = await fetch('/api/auth/logout', {
            method: 'POST',
            credentials: 'include',
            headers: {
                'X-CSRF-TOKEN': token || ''
            }
        });
        if (!response.ok) {
            console.error('Logout API call failed:', response.status, response.statusText);
        } else {
             console.log("Logout API call successful.");
        }
    } catch (error) {
        console.error('Error during logout fetch:', error);
    } finally {
        localStorage.removeItem('username');
        console.log("Redirecting to /login");
        window.location.href = '/login';
    }
}

// --- Initial Load Logic ---

window.addEventListener('load', async function() {
    // --- Select ALL logout triggers ---
    const logoutTriggers = document.querySelectorAll(
        '#nav-logout, #mobile-nav-logout, #profile-logout-button' // Added #profile-logout-button
    );
    // --- End Select ---

    // --- Attach listener to all found triggers ---
    logoutTriggers.forEach(trigger => {
        if (trigger) { // Check if element exists
            // Remove potential old inline handlers if necessary
            if (trigger.hasAttribute('onclick')) {
                trigger.removeAttribute('onclick');
                console.log(`Removed onclick from ${trigger.id || trigger.tagName}`);
            }
            // Add the event listener
            trigger.addEventListener('click', (event) => {
                event.preventDefault(); // Prevent default button/link action
                console.log(`Logout triggered by: ${trigger.id || trigger.tagName}`);
                handleLogout(); // Call the existing logout handler
            });
        }
    });
    // --- End Attach Listener ---

    // --- CSRF Fetch Logic (keep as is) ---
    const publicAuthPaths = ['/login', '/register', '/forgot-password', '/reset-password'];
    const isPublicAuthPage = publicAuthPaths.some(path => window.location.pathname.startsWith(path));

    if (!isPublicAuthPage) {
       await fetchAndStoreCSRFToken();
    } else {
       console.log("Skipping initial CSRF token fetch on public auth page.");
    }
});

// --- Global Availability ---

window.authFetch = authFetch;
window.handleLogout = handleLogout;