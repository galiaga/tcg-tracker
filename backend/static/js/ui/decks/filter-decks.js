import { updateDeckListView } from "./deck-list-manager.js";

document.addEventListener("DOMContentLoaded", function () {
    const filterSelect = document.getElementById("filter_decks");
    if(filterSelect) {
        filterSelect.addEventListener('change', updateDeckListView);
    }
});
