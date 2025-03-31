document.addEventListener("DOMContentLoaded", () => {
    const modal = document.getElementById("newDeckModal");

    if (!modal) {
        console.error("Modal container 'newDeckModal' not found.");
        return;
    }

    const modalContent = modal.querySelector(".bg-white");
    const openBtn = document.getElementById("newDeckModalButton");
    const closeBtn = document.getElementById("newDeckModalCloseButton");
    const form = document.getElementById('register-deck-form');

    if (!modalContent || !openBtn || !closeBtn || !form) {
        console.error("Modal element (content, openBtn, closeBtn, form) not found.");
        return; 
    }

    const conditionalFieldPrefixes = [
        "commander", "partner", "friendsForever",
        "doctorCompanion", "timeLordDoctor", "background"
    ];

    function resetNewDeckForm() {
        form.reset();

        conditionalFieldPrefixes.forEach(prefix => {
            const fieldDiv = document.getElementById(`${prefix}Field`);
            const suggestionsUl = document.getElementById(`${prefix}-suggestions`);

            if (fieldDiv) {
                fieldDiv.classList.add('hidden');
            }
            if (suggestionsUl) {
                suggestionsUl.innerHTML = ''; 
                suggestionsUl.style.display = 'none';
            }
        });
    }
  
    function openModal() {
      modal.classList.remove("hidden");
      setTimeout(() => {
        modalContent.classList.remove("scale-95", "opacity-0");
        modalContent.classList.add("scale-100", "opacity-100");
      }, 10);
    }
  
    function closeModal() {
        resetNewDeckForm();
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
  });
  