document.addEventListener("DOMContentLoaded", () => {
    const modal = document.getElementById("logMatchModal");

    if (!modal) {
        console.error("Modal container 'logMatchModal' not found.");
        return;
    }

    const modalContent = modal.querySelector(".bg-white");
    const openBtn = document.getElementById("logMatchModalButton");
    const closeBtn = document.getElementById("logMatchModalCloseButton");
    const form = document.getElementById('log-match-form');

    if (!modalContent || !openBtn || !closeBtn || !form) {
        console.error("Modal element (content, openBtn, closeBtn, form) for Log Match not found.");
        return;
    }

    function resetLogMatchForm() {
        if (form) {
           form.reset();
           const deckSelect = document.getElementById("deck-select");
           if (deckSelect) {
              deckSelect.value = "";
           }
           const defaultRadio = form.querySelector('input[name="match_result"][value="0"]');
            if (defaultRadio) {
                defaultRadio.checked = true;
            }
        }
    }

    function openModal() {
      modal.classList.remove("hidden");
      setTimeout(() => {
        modalContent.classList.remove("scale-95", "opacity-0");
        modalContent.classList.add("scale-100", "opacity-100");
      }, 10);
    }

    function closeModal() {
        resetLogMatchForm();
        modalContent.classList.remove("scale-100", "opacity-100");
        modalContent.classList.add("scale-95", "opacity-0");

        setTimeout(() => {
            modal.classList.add("hidden");
        }, 150); 
    }

    openBtn.addEventListener("click", openModal);
    closeBtn.addEventListener("click", closeModal);

    modal.addEventListener("click", (event) => {
      if (event.target === modal) {
        closeModal();
      }
    });

    if (form) {
        form.addEventListener('matchLoggedSuccess', closeModal);
    }

});