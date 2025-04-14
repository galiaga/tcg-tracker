function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

export async function authFetch(url, options = {}) {
    options.headers = options.headers || {};
    if (options.body && !options.headers['Content-Type']) {
         options.headers['Content-Type'] = 'application/json';
    }

    const method = options.method ? options.method.toUpperCase() : 'GET';
    const csrfCookieName = url.endsWith('/api/auth/refresh') ? 'csrf_refresh_token' : 'csrf_access_token';
    if (!['GET', 'HEAD', 'OPTIONS', 'TRACE'].includes(method)) {
        const csrfToken = getCookie(csrfCookieName);
        if (csrfToken) {
            options.headers['X-CSRF-TOKEN'] = csrfToken;
        } else {
            console.warn(`CSRF token cookie ('${csrfCookieName}') not found for state-changing request to ${url}.`);
        }
    }

    options.credentials = 'include';

    try {
        let response = await fetch(url, options);

        if (response.status === 401 && !url.endsWith('/api/auth/refresh')) {
            console.warn("authFetch: 401 Unauthorized. Attempting token refresh via cookie...");
            try {
                const csrfRefreshToken = getCookie('csrf_refresh_token');
                const refreshOptions = {
                    method: "POST",
                    credentials: 'include',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                };
                 if (csrfRefreshToken) {
                   refreshOptions.headers['X-CSRF-TOKEN'] = csrfRefreshToken;
                 } else {
                   console.warn('CSRF refresh token cookie not found for refresh request.');
                 }

                const refreshResponse = await fetch("/api/auth/refresh", refreshOptions);

                if (refreshResponse.ok) {
                    if (!['GET', 'HEAD', 'OPTIONS', 'TRACE'].includes(method)) {
                         const newCsrfToken = getCookie('csrf_access_token');
                         if (newCsrfToken) {
                              options.headers['X-CSRF-TOKEN'] = newCsrfToken;
                         } else {
                              console.warn('New CSRF access token cookie not found after refresh.');
                         }
                    }
                    response = await fetch(url, options);
                } else {
                    console.error("authFetch: Refresh token failed.");
                    handleLogout(true);
                    return Promise.reject(new Error("Token refresh failed"));
                }
            } catch (refreshError) {
                console.error("authFetch: Exception during token refresh:", refreshError);
                handleLogout(true);
                return Promise.reject(refreshError);
            }
        }

        return response;

    } catch (error) {
        console.error(`authFetch: Fetch error for ${url}:`, error);
        throw error;
    }
}

export async function handleLogout(forceRedirect = false) {
    try {
        const response = await authFetch('/api/auth/logout', {
            method: 'POST'
        });

        if (!response.ok && !forceRedirect) {
            console.error('Logout API call failed:', response.status, response.statusText);
        }

    } catch (error) {
        console.error('Error during logout fetch:', error);
    } finally {
         localStorage.removeItem('username');
         localStorage.removeItem('accessToken');
         localStorage.removeItem('refreshToken');
         window.location.href = '/login';
    }
}

window.logout = handleLogout;

window.onload = function() {

    const logoutLink = document.querySelector('#nav-logout');
    if (logoutLink) {
         if (logoutLink.getAttribute('onclick')) { logoutLink.removeAttribute('onclick'); }
         logoutLink.addEventListener('click', (event) => {
              event.preventDefault(); 
              handleLogout();  
         });
    }

    const mobileLogoutButton = document.querySelector('#mobile-navbar button[aria-label="Logout"]');
     if (mobileLogoutButton) {
          if (mobileLogoutButton.getAttribute('onclick')) { mobileLogoutButton.removeAttribute('onclick'); }
          mobileLogoutButton.addEventListener('click', (event) => {
               event.preventDefault();
               handleLogout(); 
          });
     }
};
