// static/js/ui/hideNavbar.js
document.addEventListener("DOMContentLoaded", function () {
    const path = window.location.pathname;
    const navbar = document.getElementById("main-navbar");

    if (navbar && ["/login", "/register"].includes(path)) {
        navbar.style.display = "none";
    }
});
