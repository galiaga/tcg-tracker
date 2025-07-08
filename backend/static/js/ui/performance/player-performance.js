// backend/static/js/ui/performance/player-performance.js

import { authFetch } from '../../auth/auth.js';
import { openLogMatchModal } from '../matches/log-match-modal.js';

function showLoadingState(isLoading) {
    const loadingEl = document.getElementById('performance-loading');
    const dataContainerEl = document.getElementById('performance-data-container');
    const noDataEl = document.getElementById('no-performance-data');

    if (loadingEl) loadingEl.style.display = isLoading ? 'block' : 'none';
    if (dataContainerEl) dataContainerEl.classList.toggle('hidden', isLoading);
    if (noDataEl) noDataEl.classList.add('hidden'); // Always hide no-data during load
}

function showNoDataState() {
    const noDataEl = document.getElementById('no-performance-data');
    if (noDataEl) {
        noDataEl.classList.remove('hidden');
        document.getElementById('performance-data-container').classList.add('hidden');
    }
    const logFirstMatchButton = document.getElementById('log-first-match-button');
    if (logFirstMatchButton) {
        logFirstMatchButton.addEventListener('click', () => {
            if (typeof openLogMatchModal === 'function') {
                openLogMatchModal();
            }
        });
    }
}

function renderHeadlineStats(data) {
    const overallWrEl = document.getElementById('dashboard-overall-wr');
    const totalMatchesEl = document.getElementById('dashboard-total-matches');
    const winningestDeckEl = document.getElementById('dashboard-winningest-deck');
    const mostPlayedDeckEl = document.getElementById('dashboard-most-played-deck');

    if (overallWrEl) overallWrEl.textContent = `${data.overall_win_rate}%`;
    if (totalMatchesEl) totalMatchesEl.textContent = data.total_matches;
    if (winningestDeckEl) {
        winningestDeckEl.textContent = data.winningest_deck;
        winningestDeckEl.title = data.winningest_deck;
    }
    if (mostPlayedDeckEl) {
        mostPlayedDeckEl.textContent = data.most_played_deck;
        mostPlayedDeckEl.title = data.most_played_deck;
    }
}

function renderTurnOrderStats(stats) {
    const container = document.getElementById('dashboard-turn-order-stats-container');
    if (!container) return;

    container.innerHTML = ''; // Clear previous content
    const positions = ["1st", "2nd", "3rd", "4th"];

    positions.forEach((posText, index) => {
        const posKey = String(index + 1);
        const posData = stats[posKey];
        const div = document.createElement('div');
        div.className = 'p-4 bg-white dark:bg-gray-800 text-center';

        if (posData && posData.matches > 0) {
            const winRate = parseFloat(posData.win_rate ?? 0).toFixed(0);
            let color = 'text-gray-700 dark:text-gray-200';
            if (parseFloat(winRate) >= 55) color = 'text-green-500 dark:text-green-400';
            else if (parseFloat(winRate) < 45) color = 'text-red-500 dark:text-red-400';
            else color = 'text-yellow-500 dark:text-yellow-400';

            div.innerHTML = `
                <div class="font-semibold text-gray-700 dark:text-gray-200">${posText}</div>
                <div class="text-2xl font-bold mt-1 ${color}">${winRate}%</div>
                <div class="text-xs text-gray-400 dark:text-gray-500 mt-1">(${posData.wins} W / ${posData.matches} M)</div>
            `;
        } else {
            div.innerHTML = `
                <div class="font-semibold text-gray-700 dark:text-gray-200">${posText}</div>
                <div class="text-2xl font-bold mt-1 text-gray-400 dark:text-gray-500">-</div>
                <div class="text-xs text-gray-400 dark:text-gray-500 mt-1">(0 W / 0 M)</div>
            `;
        }
        container.appendChild(div);
    });
}

async function loadPerformanceData() {
    showLoadingState(true);
    try {
        const response = await authFetch('/api/performance-summary');
        if (!response) throw new Error('Network or authentication error.');
        
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Failed to load performance data.');

        if (data.has_data) {
            renderHeadlineStats(data);
            renderTurnOrderStats(data.turn_order_stats);
        } else {
            showNoDataState();
        }

    } catch (error) {
        console.error('Error loading player performance data:', error);
        if (typeof showFlashMessage === 'function') {
            showFlashMessage(error.message, 'danger');
        }
        document.getElementById('performance-data-container').innerHTML = `<p class="text-red-500 text-center">${error.message}</p>`;
    } finally {
        showLoadingState(false);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    // Ensure we are on the player performance page before running
    if (document.getElementById('player-performance-content')) {
        loadPerformanceData();

        // Listen for a new match being logged anywhere in the app
        document.addEventListener('globalMatchLoggedSuccess', () => {
            console.log("New match logged, reloading performance data...");
            loadPerformanceData();
        });
    }
});