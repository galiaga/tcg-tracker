document.addEventListener('DOMContentLoaded', () => {
    const toggleBtn = document.getElementById('toggle-filters-btn');
    const filterControls = document.getElementById('filter-controls');
    const buttonTextSpan = toggleBtn ? toggleBtn.querySelector('#toggle-filters-text') : null; 

    if (toggleBtn && filterControls && buttonTextSpan) {

        const isInitiallyHidden = filterControls.classList.contains('hidden');
        buttonTextSpan.textContent = isInitiallyHidden ? 'Sort & Filter' : 'Hide Filters';

        toggleBtn.addEventListener('click', () => {
            filterControls.classList.toggle('hidden');
            const isHidden = filterControls.classList.contains('hidden');
            buttonTextSpan.textContent = isHidden ? 'Sort & Filter' : 'Hide Filters';
        });

    } else {
        if (!toggleBtn) {
            console.error('Button with id "toggle-filters-btn" not found.');
        }
        if (!filterControls) {
            console.error('Element with id "filter-controls" not found.');
        }
        if (!buttonTextSpan) {
            console.error('Text span with id "toggle-filters-text" inside the button not found. Make sure it exists in the HTML.');
        }
    }
});