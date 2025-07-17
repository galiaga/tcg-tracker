// backend/static/js/ui/decks/deck-details.js 

import { authFetch } from '../../auth/auth.js';
import { openQuickAddTagModal } from '../tag-utils.js';
import { openLogMatchModal } from '../matches/log-match-modal.js';

// --- Module-level variables ---
let manaCurveChartInstance = null;

let fetchDeckInfoButton = null;
let deckAnalysisContent = null;
let deckAnalysisLoading = null;

let currentDeckId = null;
let currentDeckName = null;
let currentDeckUrl = null;

let deckDetailsContentElement = null;
let deckDetailsLoadingElement = null;
let deckPageTitleElement = null;
let backToDecksButton = null;

let deckInfoStatsCardElement = null;
let quickLogCardElement = null;
let deckTagsCardElement = null;
let turnOrderStatsCardElement = null;
let recentMatchesCardElement = null;
let mulliganStatsCardElement = null;
let matchupAnalysisCardElement = null;
let decklistCardElement = null;

let deckOptionsMenuButton = null;
let deckOptionsDropdown = null;
let renameDeckButton = null;
let deleteDeckButton = null;

let renameDeckModalElement = null;
let renameDeckFormElement = null;
let renameDeckModalCloseButton = null;
let renameDeckCancelButton = null;
let newDeckNameInputElement = null;

let editDeckUrlModalElement = null;
let editDeckUrlFormElement = null;
let editDeckUrlModalCloseButton = null;
let editDeckUrlCancelButton = null;
let deckUrlInputElement = null;
let editDeckUrlButton = null;

let globalLogMatchFab = null;

// --- UI Update Functions ---
function updatePageTitle(newTitle) {
    document.title = `TCG Tracker: ${newTitle || 'Deck Details'}`;
    if (deckPageTitleElement) {
        deckPageTitleElement.textContent = newTitle || "Deck Details";
    }
}

function showLoadingState() {
    if (deckDetailsLoadingElement) deckDetailsLoadingElement.style.display = 'block';
    [deckInfoStatsCardElement, quickLogCardElement, deckTagsCardElement, turnOrderStatsCardElement, recentMatchesCardElement, 
        mulliganStatsCardElement, matchupAnalysisCardElement, decklistCardElement]
        .forEach(el => el?.classList.add('hidden'));
}

function hideLoadingState() {
    if (deckDetailsLoadingElement) deckDetailsLoadingElement.style.display = 'none';
}

// --- Card Rendering Functions ---

function renderDeckInfoStats(deckData) {
    if (!deckInfoStatsCardElement || !deckData) return;
    const winRate = parseFloat(deckData.win_rate ?? 0);
    const totalMatches = parseInt(deckData.total_matches ?? 0, 10);
    let winrateColorClass = 'text-gray-700 dark:text-gray-200';
    if (totalMatches > 0) {
        if (winRate >= 55) winrateColorClass = 'text-green-500 dark:text-green-400';
        else if (winRate < 45) winrateColorClass = 'text-red-500 dark:text-red-400';
        else winrateColorClass = 'text-yellow-500 dark:text-yellow-400';
    }
    let commanderHtml = '';
    if (deckData.commander_name) {
        commanderHtml += `<div class="py-2.5 sm:py-3 grid grid-cols-3 gap-4 px-4 sm:px-5"><dt class="text-xs font-medium text-gray-500 dark:text-gray-400">Commander</dt><dd class="mt-0 text-xs text-gray-900 dark:text-gray-100 col-span-2">${deckData.commander_name}</dd></div>`;
    }
    let assocLabel = "Associated";
    if (deckData.partner_name) assocLabel = "Partner";
    else if (deckData.friends_forever_name) assocLabel = "Friends Forever";
    else if (deckData.background_name) assocLabel = "Background";
    else if (deckData.doctor_companion_name) assocLabel = "Companion";
    else if (deckData.time_lord_doctor_name) assocLabel = "Doctor";    
    if (deckData.associated_commander_name) {
        commanderHtml += `<div class="py-2.5 sm:py-3 grid grid-cols-3 gap-4 px-4 sm:px-5 ${commanderHtml ? 'bg-gray-50/70 dark:bg-gray-700/40' : ''}"><dt class="text-xs font-medium text-gray-500 dark:text-gray-400">${assocLabel}</dt><dd class="mt-0 text-xs text-gray-900 dark:text-gray-100 col-span-2">${deckData.associated_commander_name}</dd></div>`;
    }
    deckInfoStatsCardElement.innerHTML = `<div class="border-t border-gray-200 dark:border-gray-700 first:border-t-0"><dl class="divide-y divide-gray-200 dark:divide-gray-700">${commanderHtml}<div class="py-3 sm:py-4 grid grid-cols-3 gap-4 px-4 sm:px-5 ${commanderHtml ? 'bg-gray-50/70 dark:bg-gray-700/40' : ''}"><dt class="text-sm font-semibold text-gray-600 dark:text-gray-300 self-center">Performance</dt><dd class="mt-0 text-gray-900 dark:text-gray-100 col-span-2 self-center text-right sm:text-left"><span class="${winrateColorClass} text-xl font-bold">${winRate.toFixed(1)}%</span><span class="ml-1 text-xs text-gray-500 dark:text-gray-400">WR</span><span class="mx-1.5 text-gray-300 dark:text-gray-600">|</span><span class="text-sm">${totalMatches} M / ${deckData.total_wins ?? 0} W</span></dd></div></dl></div>`;
    deckInfoStatsCardElement.classList.remove('hidden');
}

function renderDecklistCard(deckUrl) {
    if (!decklistCardElement) return;
    const container = decklistCardElement.querySelector('#decklist-display-container');
    const editButton = decklistCardElement.querySelector('#edit-deck-url-button');
    if (!container || !editButton) {
        console.error("Decklist card internal elements not found.");
        return;
    }
    if (deckUrl) {
        container.innerHTML = `<a href="${deckUrl}" target="_blank" rel="noopener noreferrer" class="text-violet-500 dark:text-violet-400 hover:underline break-all" title="Open link in new tab">${deckUrl}</a>`;
        editButton.textContent = 'Edit';
    } else {
        container.innerHTML = `<span class="text-gray-500 dark:text-gray-400 italic">No decklist link provided.</span>`;
        editButton.textContent = 'Add Link';
    }
    decklistCardElement.classList.remove('hidden');
}

function renderQuickLogButtons() {
    if (!quickLogCardElement) return;
    const container = quickLogCardElement.querySelector('#quick-log-buttons-container');
    if (!container) return;
    container.innerHTML = `<button type="button" data-result="0" class="quick-log-btn bg-green-500 hover:bg-green-600 text-white font-medium py-2 px-4 rounded-lg shadow-sm transition w-full text-sm">Win</button><button type="button" data-result="1" class="quick-log-btn bg-red-500 hover:bg-red-600 text-white font-medium py-2 px-4 rounded-lg shadow-sm transition w-full text-sm">Loss</button><button type="button" data-result="2" class="quick-log-btn bg-yellow-500 hover:bg-yellow-600 text-white font-medium py-2 px-4 rounded-lg shadow-sm transition w-full text-sm">Draw</button>`;
    quickLogCardElement.classList.remove('hidden');
}

function renderDeckTags(tags, deckId) {
    if (!deckTagsCardElement) return;
    const pillsContainer = deckTagsCardElement.querySelector('#deck-tags-pills-container-detail');
    const addButton = deckTagsCardElement.querySelector('#add-deck-tag-button-detail');
    if (!pillsContainer || !addButton) return;
    pillsContainer.innerHTML = ''; 
    if (tags && tags.length > 0) {
        tags.forEach(tag => {
            const pill = document.createElement('span');
            pill.className = 'tag-pill inline-flex items-center gap-1 bg-violet-100 dark:bg-violet-700/60 text-violet-700 dark:text-violet-300 text-xs font-medium px-2 py-0.5 rounded-full';
            pill.dataset.tagId = tag.id;
            pill.innerHTML = `<span>${tag.name}</span><button type="button" class="remove-deck-tag-button ml-0.5 -mr-0.5 flex-shrink-0 rounded-full p-0.5 text-violet-400 dark:text-violet-500 hover:bg-violet-200 dark:hover:bg-violet-600" aria-label="Remove tag ${tag.name}"><svg class="h-2 w-2" stroke="currentColor" fill="none" viewBox="0 0 8 8"><path stroke-linecap="round" stroke-width="1.5" d="M1 1l6 6m0-6L1 7" /></svg></button>`;
            pillsContainer.appendChild(pill);
        });
    } else {
        pillsContainer.innerHTML = `<span class="text-xs text-gray-500 dark:text-gray-400 italic">No tags yet.</span>`;
    }
    deckTagsCardElement.classList.remove('hidden');
}

function renderTurnOrderStats(stats) {
    if (!turnOrderStatsCardElement || !stats) return;
    const container = turnOrderStatsCardElement.querySelector('#turn-order-stats-container');
    if (!container) return;
    container.innerHTML = '';
    const positions = ["1st", "2nd", "3rd", "4th"];
    let hasAnyStats = false;
    positions.forEach((posText, index) => {
        const posKey = String(index + 1);
        const posData = stats[posKey];
        const div = document.createElement('div');
        div.className = 'p-2 bg-gray-50 dark:bg-gray-700/50 rounded-md text-center';
        if (posData && posData.matches > 0) {
            hasAnyStats = true;
            const winRate = parseFloat(posData.win_rate ?? 0).toFixed(0);
            let color = 'text-gray-700 dark:text-gray-200';
            if (parseFloat(winRate) >= 55) color = 'text-green-500 dark:text-green-400';
            else if (parseFloat(winRate) < 45) color = 'text-red-500 dark:text-red-400';
            else color = 'text-yellow-500 dark:text-yellow-400';
            div.innerHTML = `<div class="font-medium text-gray-600 dark:text-gray-300">${posText}</div><div class="text-base font-semibold ${color}">${winRate}%</div><div class="text-xxs text-gray-400 dark:text-gray-500">(${posData.wins}/${posData.matches})</div>`;
        } else {
            div.innerHTML = `<div class="font-medium text-gray-600 dark:text-gray-300">${posText}</div><div class="text-base text-gray-400 dark:text-gray-500">-</div><div class="text-xxs text-gray-400 dark:text-gray-500">(0/0)</div>`;
        }
        container.appendChild(div);
    });
    if (!hasAnyStats) { 
        container.innerHTML = `<p class="col-span-full text-xs text-gray-500 dark:text-gray-400 italic text-center py-2">No match data with turn order logged yet.</p>`;
    }
    turnOrderStatsCardElement.classList.remove('hidden');
}

function renderMulliganStats(stats) {
    const container = mulliganStatsCardElement;
    if (!container) return;
    const tableBody = container.querySelector('#mulligan-stats-tbody');
    const noDataMessage = container.querySelector('#no-mulligan-data');
    const table = tableBody ? tableBody.closest('table') : null;
    if (!tableBody || !noDataMessage || !table) {
        container.classList.add('hidden');
        return;
    }
    tableBody.innerHTML = '';
    if (stats && stats.length > 0) {
        stats.forEach(stat => {
            const winRate = stat.win_rate;
            let textColor = 'text-gray-600 dark:text-gray-300';
            if (stat.game_count > 0) {
                if (winRate >= 55) textColor = 'text-green-600 dark:text-green-400';
                else if (winRate < 45) textColor = 'text-red-600 dark:text-red-400';
                else textColor = 'text-yellow-500 dark:text-yellow-400';
            }
            const row = `<tr><td class="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-gray-100">${stat.label}</td><td class="px-4 py-3 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400 text-center">${stat.game_count}</td><td class="px-4 py-3 whitespace-nowrap text-sm font-semibold ${textColor} text-center">${winRate}%</td></tr>`;
            tableBody.insertAdjacentHTML('beforeend', row);
        });
        table.classList.remove('hidden');
        noDataMessage.classList.add('hidden');
        container.classList.remove('hidden');
    } else {
        container.classList.add('hidden');
    }
}

function renderRecentMatches(matches, deckId) {
    if (!recentMatchesCardElement) return;
    const listContainer = recentMatchesCardElement.querySelector('#recent-matches-list-container');
    const noMatchesMsg = recentMatchesCardElement.querySelector('#no-recent-matches-message');
    const viewAllBtnContainer = recentMatchesCardElement.querySelector('#view-all-matches-button-container');
    const viewAllLink = recentMatchesCardElement.querySelector('#view-all-matches-link');
    if (!listContainer || !noMatchesMsg || !viewAllBtnContainer || !viewAllLink) return;
    listContainer.innerHTML = '';
    if (matches && matches.length > 0) {
        noMatchesMsg.classList.add('hidden');
        matches.forEach(match => {
            const item = document.createElement('div');
            item.className = 'py-2 border-b border-gray-100 dark:border-gray-700/50 last:border-b-0 flex justify-between items-center text-xs';
            const resultText = match.result === 0 ? 'Win' : match.result === 1 ? 'Loss' : 'Draw';
            const resultColor = match.result === 0 ? 'text-green-500' : match.result === 1 ? 'text-red-500' : 'text-yellow-500';
            const date = match.timestamp ? new Date(match.timestamp).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' }) : 'N/A';
            item.innerHTML = `<span class="font-medium ${resultColor}">${resultText}</span><span class="text-gray-400 dark:text-gray-500">${date} (P${match.player_position || '?'})</span>`;
            listContainer.appendChild(item);
        });
        if (matches.length >= 5 && currentDeckId) { 
            viewAllLink.href = `/matches-history?deckFilters=${currentDeckId}`; 
            viewAllBtnContainer.style.display = 'block';
        } else {
            viewAllBtnContainer.style.display = 'none';
        }
    } else {
        noMatchesMsg.classList.remove('hidden');
        viewAllBtnContainer.style.display = 'none';
    }
    recentMatchesCardElement.classList.remove('hidden');
}

function renderMatchupStats(matchupData) {
    if (!matchupAnalysisCardElement) return;
    const createMatchupItem = (matchup, type) => {
        const winRateColor = type === 'nemesis' ? 'text-red-500 dark:text-red-400' : 'text-green-500 dark:text-green-400';
        return `<div class="grid grid-cols-3 gap-4 items-center py-2 border-b border-gray-700/50 last:border-b-0"><div class="col-span-2"><p class="text-sm font-medium text-white" title="${matchup.name}">${matchup.name}</p><p class="text-xs text-gray-400">${matchup.wins}W – ${matchup.losses}L</p></div><div class="text-right"><p class="text-base font-semibold ${winRateColor}">${matchup.win_rate}%</p></div></div>`;
    };
    const placeholder = matchupAnalysisCardElement.querySelector('#matchup-analysis-placeholder');
    const container = matchupAnalysisCardElement.querySelector('#matchup-analysis-container');
    if (!placeholder || !container) {
        matchupAnalysisCardElement.classList.add('hidden');
        return;
    }
    const nemesisList = container.querySelector('#nemesis-matchups-list');
    const favorableList = container.querySelector('#favorable-matchups-list');
    const hasNemesisData = matchupData && matchupData.nemesis && matchupData.nemesis.length > 0;
    const hasFavorableData = matchupData && matchupData.favorable && matchupData.favorable.length > 0;
    if (!hasNemesisData && !hasFavorableData) {
        placeholder.classList.remove('hidden');
        container.classList.add('hidden');
    } else {
        placeholder.classList.add('hidden');
        container.classList.remove('hidden');
        nemesisList.innerHTML = '';
        favorableList.innerHTML = '';
        if (hasNemesisData) {
            matchupData.nemesis.forEach(matchup => {
                nemesisList.insertAdjacentHTML('beforeend', createMatchupItem(matchup, 'nemesis'));
            });
        } else {
            nemesisList.innerHTML = '<p class="text-gray-500 text-sm">No significant nemesis matchups found.</p>';
        }
        if (hasFavorableData) {
            matchupData.favorable.forEach(matchup => {
                favorableList.insertAdjacentHTML('beforeend', createMatchupItem(matchup, 'favorable'));
            });
        } else {
            favorableList.innerHTML = '<p class="text-gray-500 text-sm">No significant favorable matchups found.</p>';
        }
    }
    matchupAnalysisCardElement.classList.remove('hidden');
}

// This is the new, single, compact chart rendering function
function renderDeckAnalysisChart(analysisData) {
    const ctx = document.getElementById('mana-curve-chart').getContext('2d');
    const typeColorMap = {
        'Creature': 'rgba(34, 197, 94, 0.7)',   // green-500
        'Instant': 'rgba(96, 165, 250, 0.7)',  // blue-400
        'Sorcery': 'rgba(139, 92, 246, 0.7)',  // violet-500
        'Artifact': 'rgba(107, 114, 128, 0.7)',// gray-500
        'Enchantment': 'rgba(239, 68, 68, 0.7)', // red-500
        'Planeswalker': 'rgba(217, 119, 6, 0.7)',// amber-600
        'Land': 'rgba(245, 158, 11, 0.7)',     // amber-500
        'Other': 'rgba(209, 213, 219, 0.7)'   // gray-300
    };
    const labels = Array.from({ length: 11 }, (_, i) => i === 10 ? '10+' : String(i));
    const datasets = Object.keys(analysisData).map(type => {
        return {
            label: type,
            data: Object.values(analysisData[type]),
            backgroundColor: typeColorMap[type] || typeColorMap['Other']
        };
    });

    if (manaCurveChartInstance) {
        manaCurveChartInstance.destroy();
    }

    manaCurveChartInstance = new Chart(ctx, {
        type: 'bar',
        data: { labels: labels, datasets: datasets },
        options: {
            plugins: {
                title: { display: false },
                legend: { position: 'bottom', labels: { color: '#d1d5db', boxWidth: 20, padding: 20 } }
            },
            responsive: true,
            scales: {
                x: { stacked: true, ticks: { color: '#9ca3af' } },
                y: { stacked: true, ticks: { color: '#9ca3af' } }
            }
        }
    });
}

async function loadDeckDetails(deckIdToLoad) {
    showLoadingState();
    currentDeckId = deckIdToLoad; 
    try {
        const response = await authFetch(`/api/decks/${deckIdToLoad}?include_turn_stats=true&include_recent_matches=5&include_mulligan_stats=true&include_matchup_stats=true`);
        if (!response.ok) {
            if (response.status === 404) throw new Error("Deck not found.");
            const errorData = await response.json().catch(() => ({ message: `Error loading deck details (${response.status})` }));
            throw new Error(errorData.error || errorData.message || `HTTP error ${response.status}`);
        }
        const deckData = await response.json();
        if (!deckData || !deckData.id) throw new Error("Received invalid deck data.");
        currentDeckName = deckData.name;
        currentDeckUrl = deckData.deck_url || null;
        updatePageTitle(deckData.name);
        renderDeckInfoStats(deckData);
        renderQuickLogButtons(); 
        renderDeckTags(deckData.tags, deckData.id);
        renderDecklistCard(deckData.deck_url);
        renderTurnOrderStats(deckData.turn_order_stats || {});
        renderMulliganStats(deckData.mulligan_stats || []);
        renderMatchupStats(deckData.matchup_stats || {});
        renderRecentMatches(deckData.recent_matches || [], deckData.id); 
        setupDeckOptionsMenuListeners(deckData);
    } catch(error) {
        console.error("[deck-details.js] Error in loadDeckDetails:", error);
        if (typeof showFlashMessage === 'function') showFlashMessage(error.message || "Failed to load deck details.", "danger");
        if (deckDetailsContentElement) deckDetailsContentElement.innerHTML = `<div class="p-6 text-center text-red-500 dark:text-red-400">${error.message || 'Error loading details.'}</div>`;
        updatePageTitle("Error");
    } finally {
        hideLoadingState();
    }
}

// --- Event Listeners & Actions ---
function setupDeckOptionsMenuListeners(deck) {
    if (!deckOptionsMenuButton || !deckOptionsDropdown || !renameDeckButton || !deleteDeckButton) return;
    deckOptionsMenuButton.onclick = (event) => {
        event.stopPropagation();
        deckOptionsDropdown.classList.toggle('hidden');
        deckOptionsMenuButton.setAttribute('aria-expanded', !deckOptionsDropdown.classList.contains('hidden'));
    };
    renameDeckButton.onclick = () => {
        deckOptionsDropdown.classList.add('hidden');
        promptForRename(deck.id, deck.name);
    };
    deleteDeckButton.onclick = () => {
        deckOptionsDropdown.classList.add('hidden');
        showDeleteConfirmation(deck.id, deck.name);
    };
}

function promptForEditUrl() {
    if (!editDeckUrlModalElement || !deckUrlInputElement || !editDeckUrlFormElement) return;
    deckUrlInputElement.value = currentDeckUrl || '';
    editDeckUrlModalElement.classList.remove('hidden');
    setTimeout(() => deckUrlInputElement.focus(), 50);
    editDeckUrlFormElement.onsubmit = async (e) => {
        e.preventDefault();
        const newUrl = deckUrlInputElement.value.trim();
        if (newUrl !== (currentDeckUrl || '')) {
            await updateDeckUrlOnServer(currentDeckId, newUrl);
        }
        closeEditUrlModal();
    };
    editDeckUrlModalElement.addEventListener('click', (event) => {
        if (event.target === editDeckUrlModalElement) closeEditUrlModal();
    });
}

function closeEditUrlModal() {
    if (editDeckUrlModalElement) editDeckUrlModalElement.classList.add('hidden');
    if (editDeckUrlFormElement) editDeckUrlFormElement.onsubmit = null;
}

async function updateDeckUrlOnServer(deckId, newUrl) {
    try {
        const response = await authFetch(`/api/decks/${deckId}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ deck_url: newUrl })
        });
        if (response.ok) {
            const result = await response.json();
            currentDeckUrl = result.deck.deck_url;
            renderDecklistCard(currentDeckUrl);
            if (typeof showFlashMessage === 'function') showFlashMessage("Decklist link updated!", "success");
        } else {
            const errorData = await response.json().catch(() => ({}));
            if (typeof showFlashMessage === 'function') showFlashMessage(`Error updating link: ${errorData.error || response.statusText}`, "danger");
        }
    } catch (error) {
        if (typeof showFlashMessage === 'function') showFlashMessage(error.message || 'Network error. Please try again.', "danger");
    }
}

function promptForRename(deckId, currentName) {
    if (!renameDeckModalElement || !newDeckNameInputElement || !renameDeckFormElement || !renameDeckModalCloseButton || !renameDeckCancelButton) return;
    newDeckNameInputElement.value = currentName;
    renameDeckModalElement.classList.remove('hidden');
    setTimeout(() => newDeckNameInputElement.focus(), 50);
    renameDeckFormElement.onsubmit = async (e) => {
        e.preventDefault();
        const newName = newDeckNameInputElement.value.trim();
        if (newName && newName !== currentName) {
            await updateDeckNameOnServer(deckId, newName);
        }
        closeRenameModal();
    };
    renameDeckModalCloseButton.onclick = closeRenameModal;
    renameDeckCancelButton.onclick = closeRenameModal;
    renameDeckModalElement.addEventListener('click', (event) => {
        if (event.target === renameDeckModalElement) closeRenameModal();
    });
}

function closeRenameModal() {
    if (renameDeckModalElement) renameDeckModalElement.classList.add('hidden');
    if (renameDeckFormElement) renameDeckFormElement.onsubmit = null;
}

async function updateDeckNameOnServer(deckId, newName) {
    try {
        const response = await authFetch(`/api/decks/${deckId}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ deck_name: newName })
        });
        if (response.ok) {
            if (typeof showFlashMessage === 'function') showFlashMessage("Deck renamed successfully!", "success");
            loadDeckDetails(deckId); 
        } else {
            const errorData = await response.json().catch(() => ({}));
            if (typeof showFlashMessage === 'function') showFlashMessage(`Error renaming deck: ${errorData.error || response.statusText}`, "danger");
        }
    } catch (error) {
        if (typeof showFlashMessage === 'function') showFlashMessage(error.message || 'Network error. Please try again.', "danger");
    }
}

function showDeleteConfirmation(deckId, deckName) {
     if (window.confirm(`Are you sure you want to delete the deck "${deckName}"? This action cannot be undone.`)) {
        deleteDeckOnServer(deckId);
    }
}

async function deleteDeckOnServer(deckId) {
    try {
        const response = await authFetch(`/api/decks/${deckId}`, { method: 'DELETE' });
        if (response.ok) {
            if (typeof showFlashMessage === 'function') showFlashMessage("Deck deleted successfully. Redirecting...", "success");
            setTimeout(() => { window.location.href = '/my-decks'; }, 1500);
        } else {
            const errorData = await response.json().catch(() => ({}));
            const message = errorData.error || errorData.msg || `Failed to delete deck (${response.statusText})`;
            if (typeof showFlashMessage === 'function') showFlashMessage(message, "danger");
        }
    } catch (error) {
        if (typeof showFlashMessage === 'function') showFlashMessage(error.message || 'Network error. Please try again.', "danger");
    }
}

async function handleFetchDeckInfo() {
    if (!currentDeckId) return;
    fetchDeckInfoButton.disabled = true;
    deckAnalysisContent.classList.add('hidden');
    deckAnalysisLoading.classList.remove('hidden');
    try {
        const response = await authFetch(`/api/decks/${currentDeckId}/fetch_metadata`, { method: 'POST' });
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to fetch deck info.');
        }
        const data = await response.json();

        const summaryEl = document.getElementById('deck-summary-stats');
        if (summaryEl) {
            const avgCmc = data.average_cmc.toFixed(2);
            summaryEl.innerHTML = `
                ${data.non_land_count} Non-Land | ${data.land_count} Land | 
                <span class="font-bold text-gray-700 dark:text-gray-200">Avg. CMC: ${avgCmc}</span>
            `;
        }

        renderDeckAnalysisChart(data.analysis);
        deckAnalysisContent.classList.remove('hidden');
    } catch (error) {
        console.error("Error fetching deck analysis:", error);
        if (typeof showFlashMessage === 'function') showFlashMessage(error.message, 'danger');
    } finally {
        fetchDeckInfoButton.disabled = false;
        deckAnalysisLoading.classList.add('hidden');
    }
}

function initializePageEventListeners() {
    if (quickLogCardElement) {
        quickLogCardElement.addEventListener('click', (event) => {
            const button = event.target.closest('.quick-log-btn');
            if (button && currentDeckId && currentDeckName) {
                const resultValue = button.dataset.result;
                if (typeof openLogMatchModal === 'function') {
                    openLogMatchModal({ id: currentDeckId, name: currentDeckName, result: parseInt(resultValue, 10) });
                }
            }
        });
    }
    if (fetchDeckInfoButton) {
        fetchDeckInfoButton.addEventListener('click', handleFetchDeckInfo);
    }
    if (deckTagsCardElement) {
        deckTagsCardElement.addEventListener('click', async (event) => {
            const addButton = event.target.closest('#add-deck-tag-button-detail');
            const removeButton = event.target.closest('.remove-deck-tag-button');
            if (addButton && currentDeckId) {
                if (typeof openQuickAddTagModal === 'function') {
                    openQuickAddTagModal(currentDeckId, 'deck', () => loadDeckDetails(currentDeckId));
                }
            } else if (removeButton && currentDeckId) {
                const tagPill = removeButton.closest('.tag-pill');
                const tagId = tagPill?.dataset.tagId;
                if (!tagId) return;
                try {
                    const response = await authFetch(`/api/decks/${currentDeckId}/tags/${tagId}`, { method: 'DELETE' });
                    if (response.ok) loadDeckDetails(currentDeckId);
                    else { 
                        const err = await response.json().catch(() => ({error: "Failed to remove tag"}));
                        if(typeof showFlashMessage === 'function') showFlashMessage(err.error || "Could not remove tag.", "danger");
                    }
                } catch (err) { 
                    console.error("Error removing tag:", err);
                    if(typeof showFlashMessage === 'function') showFlashMessage("Could not remove tag.", "danger");
                }
            }
        });
    }
    if (editDeckUrlButton) {
        editDeckUrlButton.addEventListener('click', promptForEditUrl);
    }
    if (editDeckUrlModalCloseButton) {
        editDeckUrlModalCloseButton.addEventListener('click', closeEditUrlModal);
    }
    if (editDeckUrlCancelButton) {
        editDeckUrlCancelButton.addEventListener('click', closeEditUrlModal);
    }
    document.addEventListener('click', (event) => {
        if (deckOptionsMenuButton && deckOptionsDropdown && 
            !deckOptionsMenuButton.contains(event.target) && 
            !deckOptionsDropdown.contains(event.target)) {
            deckOptionsDropdown.classList.add('hidden');
            deckOptionsMenuButton.setAttribute('aria-expanded', 'false');
        }
    });
}

document.addEventListener("DOMContentLoaded", () => {
    deckPageTitleElement = document.getElementById("deck-page-title");
    deckDetailsContentElement = document.getElementById("deck-details-content");
    deckDetailsLoadingElement = document.getElementById('deck-details-loading');
    backToDecksButton = document.getElementById('back-to-decks-btn');
    deckInfoStatsCardElement = document.getElementById('deck-info-stats-card');
    quickLogCardElement = document.getElementById('quick-log-card');
    deckTagsCardElement = document.getElementById('deck-tags-card');
    turnOrderStatsCardElement = document.getElementById('turn-order-stats-card');
    recentMatchesCardElement = document.getElementById('recent-matches-card');
    mulliganStatsCardElement = document.getElementById('mulligan-stats-container');
    matchupAnalysisCardElement = document.getElementById('matchup-analysis-card');
    decklistCardElement = document.getElementById('decklist-card');
    deckOptionsMenuButton = document.getElementById('deck-options-menu-button');
    deckOptionsDropdown = document.getElementById('deck-options-dropdown');
    renameDeckButton = document.getElementById('rename-deck-button'); 
    deleteDeckButton = document.getElementById('delete-deck-button'); 
    renameDeckModalElement = document.getElementById('renameDeckModal');
    renameDeckFormElement = document.getElementById('rename-deck-form');
    renameDeckModalCloseButton = document.getElementById('renameDeckModalCloseButton');
    renameDeckCancelButton = document.getElementById('renameDeckCancelButton');
    newDeckNameInputElement = document.getElementById('new_deck_name');
    editDeckUrlModalElement = document.getElementById('editDeckUrlModal');
    editDeckUrlFormElement = document.getElementById('edit-deck-url-form');
    editDeckUrlModalCloseButton = document.getElementById('editDeckUrlModalCloseButton');
    editDeckUrlCancelButton = document.getElementById('editDeckUrlCancelButton');
    deckUrlInputElement = document.getElementById('deck_url_input');
    editDeckUrlButton = document.getElementById('edit-deck-url-button');
    fetchDeckInfoButton = document.getElementById('fetch-deck-info-button');
    deckAnalysisContent = document.getElementById('deck-analysis-content');
    deckAnalysisLoading = document.getElementById('deck-analysis-loading');
    globalLogMatchFab = document.getElementById('globalLogMatchFab');

    if (!deckDetailsContentElement) return; 

    const pathParts = window.location.pathname.split("/");
    const idSlug = pathParts[pathParts.length - 1];
    let deckIdToLoad;

    try {
        const potentialId = idSlug.match(/^(\d+)/);
        if (potentialId && potentialId[1]) {
            deckIdToLoad = parseInt(potentialId[1], 10);
            if (isNaN(deckIdToLoad)) throw new Error("Parsed Deck ID is NaN from slug.");
        } else {
            const urlParams = new URLSearchParams(window.location.search);
            const idFromQuery = parseInt(urlParams.get('id'), 10);
            if (idFromQuery && !isNaN(idFromQuery)) {
                deckIdToLoad = idFromQuery;
            } else {
                throw new Error("No numeric ID found in URL slug or query parameters.");
            }
        }
    } catch(e) {
         console.error("Invalid Deck ID in URL:", idSlug, e);
         if (typeof showFlashMessage === 'function') showFlashMessage("Invalid Deck ID in URL.", "danger");
         if (deckDetailsContentElement) deckDetailsContentElement.innerHTML = '<div class="p-6 text-center text-red-500 dark:text-red-400">Invalid Deck ID in URL.</div>';
         updatePageTitle("Invalid Deck");
         return;
     }

    if (deckIdToLoad) {
        loadDeckDetails(deckIdToLoad);
        initializePageEventListeners(); 
    } else {
        console.error("[deck-details.js] Deck ID could not be determined. Cannot load details.");
        if (deckDetailsContentElement) deckDetailsContentElement.innerHTML = '<div class="p-6 text-center text-red-500 dark:text-red-400">Could not determine Deck ID.</div>';
        updatePageTitle("Error");
    }
    
    document.addEventListener('globalMatchLoggedSuccess', (event) => {
        if (currentDeckId && event.detail && typeof event.detail.deckId !== 'undefined') {
            const eventDeckId = parseInt(event.detail.deckId, 10);
            if (eventDeckId === currentDeckId) {
                console.log("[deck-details.js] Refreshing deck details due to new match logged for this deck.");
                loadDeckDetails(currentDeckId)
                    .catch(err => console.error("[deck-details.js] Error reloading deck details after match log:", err));
            }
        }
    });
});