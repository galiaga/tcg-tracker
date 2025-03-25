document.addEventListener("DOMContentLoaded", function () {
    const token = localStorage.getItem("access_token");
    const username = localStorage.getItem("username");

    const showElement = (id) => {
        const element = document.getElementById(id);
        if (element) element.classList.remove("hidden");
    };
    
    const hideElement = (id) => {
        const element = document.getElementById(id);
        if (element) element.classList.add("hidden");
    };

    if (token) {
        if (username) {
            const navUsername = document.getElementById("nav-username");
            if (navUsername) {
                navUsername.innerText = `Hey, ${username}!`;
                showElement("nav-username");
            }
        }
        hideElement("nav-login");
        hideElement("nav-register");
        showElement("nav-home");
        showElement("nav-matches");
        showElement("nav-my-decks");
        showElement("nav-logout");
    } else {
        hideElement("nav-username");
        hideElement("nav-login");
        hideElement("nav-register");
        hideElement("nav-home");
        hideElement("nav-matches");
        hideElement("nav-my-decks");
        hideElement("nav-logout");
    }

    const currentPath = window.location.pathname;

    document.querySelectorAll('.desktop-nav-link').forEach(link => {
        const expectedPath = link.getAttribute('data-path');
        const currentPath = window.location.pathname;
        
        if (expectedPath === currentPath) {
            link.classList.add('bg-blue-700', 'text-white', 'font-bold', 'rounded-full');
        } else {
            link.classList.remove('bg-blue-700', 'text-white', 'font-bold', 'rounded-full');
        }
    });
});

function logout() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("username");
    window.location.href = "/login";
}
