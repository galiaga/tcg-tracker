document.addEventListener("DOMContentLoaded", function () {

    const currentPath = window.location.pathname;

    const desktopActiveClasses = ['bg-violet-700', 'text-white', 'font-bold', 'rounded-full'];
    const mobileActiveClasses = ['bg-violet-700', 'text-white', 'font-bold', 'rounded-full']; 

    const desktopLinks = document.querySelectorAll('.desktop-nav-link');
    desktopLinks.forEach(link => {
        const linkPath = link.dataset.path; 
        let isActive = false;

        if (linkPath === '/my-decks') {
            isActive = (currentPath === '/') || currentPath.startsWith('/my-decks') || currentPath.startsWith('/decks/');
        } else if (linkPath === '/') {
             isActive = (currentPath === '/'); 
        } else if (linkPath) { 
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

        if (linkPath === '/my-decks') {
            isActive = (currentPath === '/') || currentPath.startsWith('/my-decks') || currentPath.startsWith('/decks/');
        } else if (linkPath === '/') {
            isActive = (currentPath === '/');
        } else if (linkPath) {
            isActive = currentPath.startsWith(linkPath);
        }

        if (isActive) {
            link.classList.add(...mobileActiveClasses);
        } else {
            link.classList.remove(...mobileActiveClasses);
        }
    });

});