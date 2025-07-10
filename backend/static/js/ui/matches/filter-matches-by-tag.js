// backend/static/js/ui/matches/filter-matches-by-tag.js

import { updateMatchHistoryView } from "./match-list-manager.js";
import {
    populateTagFilter,
    updateButtonText,
    toggleDropdown,
    clearTagSelection
} from '../tag-filter.js';

document.addEventListener("DOMContentLoaded", () => {

    const matchFilterConfig = {
        optionsContainerId: 'match-tag-filter-options',
        filterButtonId: 'match-tag-filter-button',
        buttonTextElementId: 'match-tag-filter-button-text',
        clearButtonId: 'clear-match-tag-filter-button',
        dropdownId: 'match-tag-filter-dropdown',
        checkboxName: 'match_tag_filter',
        checkboxIdPrefix: 'match-tag-filter',
        buttonDefaultText: "Filter by Tag",
        onFilterChange: () => {
            updateButtonText(matchFilterConfig);
            updateMatchHistoryView();
        },
        onClear: () => {
            updateButtonText(matchFilterConfig);
            updateMatchHistoryView();
        }
    };

    const filterButton = document.getElementById(matchFilterConfig.filterButtonId);
    const clearButton = document.getElementById(matchFilterConfig.clearButtonId);
    const dropdown = document.getElementById(matchFilterConfig.dropdownId);

    if (!filterButton || !clearButton || !dropdown) {
        console.error("Error: No se encontraron uno o más elementos esenciales del UI del filtro de tags para matches. IDs esperados:",
            matchFilterConfig.filterButtonId, matchFilterConfig.clearButtonId, matchFilterConfig.dropdownId);
        return;
    }

    populateTagFilter(matchFilterConfig);

    filterButton.addEventListener('click', (e) => {
        e.stopPropagation();
        toggleDropdown(matchFilterConfig);
    });

    clearButton.addEventListener('click', (e) => {
        e.stopPropagation();
        clearTagSelection(matchFilterConfig);
    });

    document.addEventListener('click', (event) => {
        if (dropdown && !dropdown.classList.contains('hidden') &&
            !filterButton.contains(event.target) &&
            !dropdown.contains(event.target))
        {
            toggleDropdown(matchFilterConfig, false);
        }
    });

});