document.addEventListener('DOMContentLoaded', () => {
    const toggleBtn = document.getElementById('toggle-match-filters-btn');
    const filterControls = document.getElementById('match-filter-controls');
    const buttonTextSpan = toggleBtn ? toggleBtn.querySelector('#toggle-match-filters-text') : null;

    if (toggleBtn && filterControls && buttonTextSpan) {

        const isInitiallyHidden = filterControls.classList.contains('hidden');
        buttonTextSpan.textContent = isInitiallyHidden ? 'Filter' : 'Hide Filters';

        toggleBtn.addEventListener('click', () => {
            filterControls.classList.toggle('hidden');
            const isHidden = filterControls.classList.contains('hidden');
            buttonTextSpan.textContent = isHidden ? 'Filter' : 'Hide Filters';
        });

    } else {
        if (!toggleBtn) console.error('Button with id "toggle-match-filters-btn" not found.');
        if (!filterControls) console.error('Element with id "match-filter-controls" not found.');
        if (!buttonTextSpan) console.error('Text span with id "toggle-match-filters-text" inside the button not found.');
    }
});