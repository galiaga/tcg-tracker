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
        warning: "bg-yellow-400 text-black",
        info: "bg-violet-700"
    };

    container.className = `transform transition-all duration-300 ease-out opacity-0 translate-y-[-20px] inline-flex items-center gap-2 px-4 py-3 text-sm text-white rounded-full shadow-lg pointer-events-auto max-w-fit md:max-w-md ${bgColors[type] || bgColors.info}`;

    text.textContent = message;
    container.classList.remove("hidden");

    requestAnimationFrame(() => {
        container.classList.remove("opacity-0", "translate-y-[-20px]");
        container.classList.add("opacity-100", "translate-y-0");
    });

    if (duration > 0) {
        setTimeout(() => {
            container.classList.remove("opacity-100", "translate-y-0");
            container.classList.add("opacity-0", "translate-y-[-20px]");
            setTimeout(() => container.classList.add("hidden"), 300);
        }, duration);
    }

    closeBtn.onclick = () => {
        container.classList.remove("opacity-100", "translate-y-0");
        container.classList.add("opacity-0", "translate-y-[-20px]");
        setTimeout(() => container.classList.add("hidden"), 300);
    };
}
