document.addEventListener("DOMContentLoaded", function() {
    const flashMessage = sessionStorage.getItem("flashMessage");
    const flashType = sessionStorage.getItem("flashType");

    if (flashMessage) {
        showFlashMessage(flashMessage, flashType);
        // Limpiar los datos de sessionStorage inmediatamente
        sessionStorage.removeItem("flashMessage");
        sessionStorage.removeItem("flashType");
    }
});

function showFlashMessage(message, type = "success") {
    const flashMessageDiv = document.getElementById("flash-message");
    const flashMessageText = document.getElementById("flash-message-text");
    
    if (!flashMessageDiv || !flashMessageText) {
        console.error("Flash message elements not found in the DOM");
        return;
    }

    // Map bootstrap alert types
    const alertTypes = {
        success: "alert-success",
        error: "alert-danger",
        warning: "alert-warning",
        info: "alert-info"
    };

    // Reset any existing timers
    if (flashMessageDiv.hideTimeout) {
        clearTimeout(flashMessageDiv.hideTimeout);
        clearTimeout(flashMessageDiv.removeTimeout);
    }

    // Apply appropriate class and set text
    flashMessageDiv.className = `alert alert-dismissible fade ${alertTypes[type] || "alert-info"}`;
    flashMessageText.textContent = message;
    
    // Show the message (trigger reflow before adding the 'show' class for smooth animation)
    flashMessageDiv.style.display = "block";
    flashMessageDiv.offsetHeight; // Force reflow
    flashMessageDiv.classList.add("show");
    
    // Set a timeout to hide the message
    flashMessageDiv.hideTimeout = setTimeout(() => {
        flashMessageDiv.classList.remove("show");
        
        flashMessageDiv.removeTimeout = setTimeout(() => {
            flashMessageDiv.style.display = "none";
        }, 150); // Transition duration
    }, 3000);
}