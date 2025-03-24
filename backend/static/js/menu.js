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
        showElement("nav-log_match");
        showElement("nav-my-decks");
        showElement("nav-logout");
    } else {
        hideElement("nav-username");
        hideElement("nav-login");
        hideElement("nav-register");
        hideElement("nav-home");
        hideElement("nav-profile");
        hideElement("nav-matches");
        hideElement("nav-log_match");
        hideElement("nav-my-decks");
        hideElement("nav-logout");
    }
});


// Función de logout
function logout() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("username");
    window.location.href = "/login";
}
