document.addEventListener("DOMContentLoaded", function () {
    const token = localStorage.getItem("access_token");
    const username = localStorage.getItem("username");

    // Función para mostrar/ocultar elementos de forma segura
    const showElement = (id) => {
        const element = document.getElementById(id);
        if (element) element.classList.add("show");
    };
    
    const hideElement = (id) => {
        const element = document.getElementById(id);
        if (element) element.classList.remove("show");
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
        showElement("nav-profile");
        showElement("nav-matches");
        showElement("nav-my-decks");
        showElement("nav-logout");
        showElement("mobile-navbar");
    } else {
        hideElement("nav-username");
        hideElement("nav-login");
        hideElement("nav-register");
        hideElement("nav-home");
        hideElement("nav-profile");
        hideElement("nav-matches");
        hideElement("nav-my-decks");
        hideElement("nav-logout");
        hideElement("mobile-navbar");
    }

    const currentPath = window.location.pathname;

    document.querySelectorAll('.mobile-nav-link').forEach(link => {
        const expectedPath = link.getAttribute('data-path');

        link.classList.remove("text-blue-800", "font-bold");
        link.querySelectorAll(".active-indicator").forEach(el => el.remove());
    
        if (expectedPath === currentPath) {
            link.classList.add("bg-blue-100", "text-blue-800", "font-bold", "rounded-full");

            const indicator = document.createElement("div");
            indicator.className = "active-indicator absolute top-0 left-0 w-full h-1 bg-blue-800 rounded-t transition-all duration-300";
            link.appendChild(indicator);
        }
    });

    document.querySelectorAll('.desktop-nav-link').forEach(link => {
        const expectedPath = link.getAttribute('data-path');
    
        link.classList.remove("text-blue-800", "font-bold");
        
        if (expectedPath === currentPath) {
            link.classList.add("bg-blue-100", "text-blue-800", "font-bold", "rounded-full");
        } else {
            link.classList.remove("bg-blue-100", "text-blue-800", "font-bold", "rounded-full");
        }
    });
    

});

function logout() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("username");
    window.location.href = "/login";
}
