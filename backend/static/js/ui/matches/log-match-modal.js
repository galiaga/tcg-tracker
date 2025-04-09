const modal = document.getElementById("logMatchModal");
const modalContent = modal?.querySelector(".bg-white");
const closeBtn = document.getElementById("logMatchModalCloseButton");
const form = document.getElementById('log-match-form');
const deckSelect = document.getElementById("deck-select");

if (!modal || !modalContent || !closeBtn || !form || !deckSelect) {
    console.error("Log Match Modal critical elements not found (modal, content, closeBtn, form, deckSelect).");
}

let preselectedDeckInfo = null;

function resetLogMatchForm() {
    if (form) {
        form.reset();
    }
    if (typeof clearMatchTagInput === 'function') {
        clearMatchTagInput();
    }
    if (deckSelect) {
        deckSelect.value = "";
        deckSelect.disabled = false;
    }
    const defaultRadio = form?.querySelector('input[name="match_result"][value="0"]');
    if (defaultRadio) {
        defaultRadio.checked = true;
    }
    preselectedDeckInfo = null;
}

function applyPreselection() {
    if (preselectedDeckInfo && deckSelect) {
        const deckIdToSelect = preselectedDeckInfo.id;
        const optionExists = deckSelect.querySelector(`option[value="${deckIdToSelect}"]`);

        if (optionExists) {
            deckSelect.value = deckIdToSelect;
            deckSelect.disabled = true;
            preselectedDeckInfo = null; 
        } else {
            console.warn(`Option for preselected deck ${deckIdToSelect} not found yet. Retrying might be needed if load is slow.`);
        }
    } else if (deckSelect) {
        deckSelect.disabled = false;
    }
}

export function openLogMatchModal(preselectedDeck = null) {
    if (!modal || !modalContent) {
        console.error("Cannot open Log Match Modal: Elements not found.");
        return;
    }

    preselectedDeckInfo = preselectedDeck;

    if (typeof initializeMatchTagInput === 'function') {
        initializeMatchTagInput();
    } else {
         console.warn("initializeMatchTagInput not available when opening modal.");
     }

    applyPreselection();

    modal.classList.remove("hidden");
    setTimeout(() => {
        modalContent?.classList.remove("scale-95", "opacity-0");
        modalContent?.classList.add("scale-100", "opacity-100");
    }, 10);
}

export function closeLogMatchModal() {
    if (!modal || !modalContent) return;

    resetLogMatchForm();
    modalContent.classList.remove("scale-100", "opacity-100");
    modalContent.classList.add("scale-95", "opacity-0");

    setTimeout(() => {
        modal.classList.add("hidden");
    }, 150);
}

if (modal && closeBtn && form) {
    closeBtn.addEventListener("click", closeLogMatchModal);

    modal.addEventListener("click", (event) => {
        if (event.target === modal) {
            closeLogMatchModal();
        }
    });

    form.addEventListener('matchLoggedSuccess', closeLogMatchModal);
}

document.addEventListener('deckOptionsLoaded', applyPreselection);