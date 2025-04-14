import { TagInputManager } from '../tagInput.js'; 
import { fetchUserTags } from '../tag-utils.js'; 

const modal = document.getElementById("logMatchModal");
const modalContent = modal?.querySelector(".bg-white");
const closeBtn = document.getElementById("logMatchModalCloseButton");
const form = document.getElementById('log-match-form');
const deckSelect = document.getElementById("deck-select");

if (!modal || !modalContent || !closeBtn || !form || !deckSelect) {
    console.error("Log Match Modal critical elements not found. Modal functionality might be broken.");
}

let preselectedDeckInfo = null;
let matchTagInputInstance = null;

function resetLogMatchForm() {
    if (form) {
        form.reset();
    }
    if (matchTagInputInstance) {
        matchTagInputInstance.clearTags(); 
    } else {
        console.warn("[log-match-modal] Cannot clear match tags: instance not found.");
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
            console.warn(`[log-match-modal] Option for preselected deck ${deckIdToSelect} not found in dropdown yet.`);
        }
    } else if (deckSelect) {
        deckSelect.disabled = false;
    }
}

export function openLogMatchModal(preselectedDeck = null) {
    if (!modal || !modalContent) {
        console.error("Cannot open Log Match Modal: Modal elements not found.");
        return;
    }

    preselectedDeckInfo = preselectedDeck;

    if (typeof TagInputManager !== 'undefined' && typeof TagInputManager.init === 'function') {
        if (matchTagInputInstance && typeof matchTagInputInstance.destroy === 'function') {
            matchTagInputInstance.destroy();
        }
        matchTagInputInstance = TagInputManager.init({
            inputId: 'match-tags-input',
            suggestionsId: 'match-tags-suggestions',
            containerId: 'match-tags-container', 

            fetchSuggestions: async (query) => {
                const tags = await fetchUserTags();
                if (!tags) return [];
                return tags.filter(tag => tag.name.toLowerCase().includes(query.toLowerCase()));
            },
        });

        if (matchTagInputInstance) {
            matchTagInputInstance.clearTags(); 
            const inputElement = document.getElementById('match-tags-input');
            if (inputElement) {
                 setTimeout(() => inputElement.focus(), 50); 
            }
        } else {
            console.error("[log-match-modal] Failed to initialize TagInputManager instance for match modal.");
        }

    } else {
        console.error("[log-match-modal] TagInputManager class or init method not found/imported.");
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

    if (matchTagInputInstance && typeof matchTagInputInstance.destroy === 'function') {
        matchTagInputInstance.destroy();
    }
    matchTagInputInstance = null; 

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
     form.addEventListener('matchLoggedSuccess', () => {
        closeLogMatchModal();
    });

} else {
    console.warn("[log-match-modal] Could not attach standard modal event listeners.");
}

document.addEventListener('deckOptionsLoaded', () => {
    applyPreselection();
});
