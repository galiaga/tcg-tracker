document.addEventListener("DOMContentLoaded", function () {
    const token = localStorage.getItem("access_token");
    const username = localStorage.getItem("username");

    const navUsername = document.getElementById("nav-username");
    const navLogin = document.getElementById("nav-login");
    const navRegister = document.getElementById("nav-register");
    const navHome = document.getElementById("nav-home");
    const navProfile = document.getElementById("nav-profile");
    const navLogMatch = document.getElementById("nav-log_match");
    const navRegisterDeck = document.getElementById("nav-register_deck");
    const navLogout = document.getElementById("nav-logout");

    if (token) {
        // Si está autenticado, mostrar username y ocultar login/register
        if (username) {
            navUsername.innerText = `Hey, ${username}!`;
        }
        navUsername.style.display = "block";
        navLogin.style.display = "none";
        navRegister.style.display = "none";
        navHome.style.display = "block";
        navProfile.style.display = "block";
        navLogMatch.style.display = "block";
        navRegisterDeck.style.display = "block";
        navLogout.style.display = "block";
    } else {
        // Si no está autenticado, mostrar login/register y ocultar username
        navUsername.style.display = "none";
        navLogin.style.display = "block";
        navRegister.style.display = "block";
        navHome.style.display = "none";
        navProfile.style.display = "none";
        navLogMatch.style.display = "none";
        navRegisterDeck.style.display = "none";
        navLogout.style.display = "none";
    }
});

// Función de logout
function logout() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("username");
    window.location.href = "/login";
}
