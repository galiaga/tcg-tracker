document.addEventListener("DOMContentLoaded", function () {
    const currentPath = window.location.pathname;

    // --- Define Active Classes (adjust these to your exact styling) ---
    // For Desktop: Your current classes seem to be for a pill-shaped background.
    // If you only want text color change like 'text-violet-200', 'font-semibold', adjust here.
    const desktopActiveClasses = ['text-violet-200', 'font-semibold']; // Example: Brighter text, bold
    const desktopInactiveClasses = []; // Add classes to remove if active ones are different from default

    // For Mobile: Based on your screenshot, active is a solid violet background.
    const mobileActiveClasses = ['bg-violet-600', 'text-white', 'dark:bg-violet-500', 'dark:text-white']; // Solid violet bg, white text
    // Default/inactive classes that should be present when NOT active.
    // These should match what's in your layout.html for these links by default.
    const mobileInactiveClasses = ['text-violet-700', 'dark:text-violet-300', 'hover:bg-violet-100', 'dark:hover:bg-violet-700'];


    // --- Helper function to apply active state ---
    function applyActiveState(links, activeClasses, inactiveClasses) {
        let bestMatchLink = null;
        let longestMatchLength = 0;

        links.forEach(link => {
            const linkPath = link.dataset.path;
            if (!linkPath) return; // Skip links without data-path

            // 1. Exact match is highest priority
            if (currentPath === linkPath) {
                bestMatchLink = link;
                longestMatchLength = Infinity; // Mark as exact match to win over startsWith
                return; // Found exact, no need to check further for this link in this loop iteration
            }

            // 2. If not an exact match yet, check for startsWith
            //    and prioritize the longest matching path.
            if (longestMatchLength !== Infinity && currentPath.startsWith(linkPath)) {
                if (linkPath.length > longestMatchLength) {
                    bestMatchLink = link;
                    longestMatchLength = linkPath.length;
                }
            }
        });

        // Apply classes based on the best match
        links.forEach(link => {
            link.classList.remove(...activeClasses, ...inactiveClasses); // Clear previous states

            if (link === bestMatchLink) {
                link.classList.add(...activeClasses);
            } else {
                link.classList.add(...inactiveClasses); // Re-apply default/inactive classes
            }
        });
        return bestMatchLink; // Return the link that was activated
    }

    // --- Process Desktop Links ---
    const desktopLinks = document.querySelectorAll('.desktop-nav-link');
    let activatedDesktopLink = applyActiveState(desktopLinks, desktopActiveClasses, desktopInactiveClasses);

    // --- Process Mobile Links ---
    const mobileLinks = document.querySelectorAll('.mobile-nav-link');
    let activatedMobileLink = applyActiveState(mobileLinks, mobileActiveClasses, mobileInactiveClasses);

    // --- Special Handling for Root Path ("/") if no specific link was activated ---
    // This makes "My Decks" active if the user is at the root path.
    if (currentPath === '/') {
        if (!activatedDesktopLink) {
            const defaultDesktopLink = document.querySelector('.desktop-nav-link[data-path="/my-decks"]');
            if (defaultDesktopLink) {
                desktopLinks.forEach(link => link.classList.remove(...desktopActiveClasses, ...desktopInactiveClasses)); // Clear others
                defaultDesktopLink.classList.add(...desktopActiveClasses); // Activate default
            }
        }
        if (!activatedMobileLink) {
            const defaultMobileLink = document.querySelector('.mobile-nav-link[data-path="/my-decks"]');
            if (defaultMobileLink) {
                mobileLinks.forEach(link => link.classList.remove(...mobileActiveClasses, ...mobileInactiveClasses)); // Clear others
                defaultMobileLink.classList.add(...mobileActiveClasses); // Activate default
            }
        }
    }
});