document.addEventListener("DOMContentLoaded", function () {
    const flashMessage = sessionStorage.getItem("flashMessage");
    const flashType = sessionStorage.getItem("flashType");

    if (flashMessage) {
        showFlashMessage(flashMessage, flashType || "info");
        sessionStorage.removeItem("flashMessage");
        sessionStorage.removeItem("flashType");
    }
});

function showFlashMessage(message, type = "info", duration = 3000) {
    const container = document.getElementById("flash-message");
    const text = document.getElementById("flash-message-text");
    const closeBtn = document.getElementById("flash-message-close");

    const bgColors = {
        success: "bg-green-500",
        error: "bg-red-500",
        warning: "bg-yellow-500 text-black",
        info: "bg-blue-500"
    };

    // Reset classes
    container.className = `max-w-md w-full rounded-xl px-4 py-3 shadow-lg pointer-events-auto transition duration-300 ease-in-out ${bgColors[type] || bgColors.info}`;
    text.textContent = message;

    container.classList.remove("hidden");

    // Close manually
    closeBtn.onclick = () => {
        container.classList.add("hidden");
    };

    // Auto-hide
    if (duration > 0) {
        setTimeout(() => {
            container.classList.add("hidden");
        }, duration);
    }
}
