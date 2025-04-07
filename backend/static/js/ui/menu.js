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
        showElement("nav-login");
        showElement("nav-register");
        hideElement("nav-home");
        hideElement("nav-matches");
        hideElement("nav-my-decks");
        hideElement("nav-logout");
        showElement("mobile-navbar");
    }

    const currentPath = window.location.pathname;

    const desktopActiveClasses = ['bg-blue-600', 'text-white', 'font-bold', 'rounded-full'];
    const mobileActiveClasses = ['bg-blue-600', 'text-white', 'font-bold', 'rounded-full']; 

    const desktopLinks = document.querySelectorAll('.desktop-nav-link');
    desktopLinks.forEach(link => {
        const linkPath = link.dataset.path;
        let isActive = false;

        if (linkPath === '/') {
             isActive = (currentPath === linkPath);
        } else if (linkPath === '/my-decks') {
            isActive = currentPath.startsWith('/my-decks') || currentPath.startsWith('/decks/');
        } else {
             isActive = currentPath.startsWith(linkPath);
        }


        if (isActive) {
            link.classList.add(...desktopActiveClasses);
        } else {
            link.classList.remove(...desktopActiveClasses);
        }
    });

    const mobileLinks = document.querySelectorAll('.mobile-nav-link');
    mobileLinks.forEach(link => {
        const linkPath = link.dataset.path;
        let isActive = false;

        if (linkPath === '/') {
            isActive = (currentPath === linkPath);
        } else if (linkPath === '/my-decks') {
            isActive = currentPath.startsWith('/my-decks') || currentPath.startsWith('/decks/');
        } else {
            isActive = currentPath.startsWith(linkPath);
        }

        if (isActive) {
            link.classList.add(...mobileActiveClasses);
        } else {
            link.classList.remove(...mobileActiveClasses);
        }
    });
});

function logout(event) {
    localStorage.removeItem("access_token");
    localStorage.removeItem("username");
    window.location.href = "/login";
}