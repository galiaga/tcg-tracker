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
        showElement("mobile-navbar");
    } else {
        hideElement("nav-username");
        hideElement("nav-login");
        hideElement("nav-register");
        hideElement("nav-home");
        hideElement("nav-matches");
        hideElement("nav-my-decks");
        hideElement("nav-logout");
        hideElement("mobile-navbar");
    }

    const currentPath = window.location.pathname;

    document.querySelectorAll('.desktop-nav-link, .mobile-nav-link').forEach(link => {
        link.classList.remove('bg-blue-600', 'text-white', 'font-bold', 'rounded-md');
    });

    const desktopLinks = document.querySelectorAll('.desktop-nav-link');
    const mobileLinks = document.querySelectorAll('.mobile-nav-link');

    desktopLinks.forEach(link => {
        const expectedPath = link.getAttribute('data-path');
        if (currentPath === expectedPath) {
            link.classList.add('bg-blue-600', 'text-white', 'font-bold', 'rounded-full');
        }
    });

    mobileLinks.forEach(link => {
        const expectedPath = link.getAttribute('data-path');
        if (currentPath === expectedPath) {
            link.classList.add('bg-blue-600', 'text-white');
        } else {
            link.classList.remove('bg-blue-600', 'text-white');
        }
    });
});

function logout() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("username");
    window.location.href = "/login";
}