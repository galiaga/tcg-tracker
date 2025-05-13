// backend/static/js/ui/tournaments/tournament_form.js

document.addEventListener('DOMContentLoaded', function () {
    // --- Flatpickr for Event Date ---
    const eventDateInput = document.getElementById('event_date');

    if (eventDateInput) {
        flatpickr(eventDateInput, {
            enableTime: true,
            dateFormat: "Y-m-d H:i", // MATCHES WTForms: %Y-%m-%d %H:%M
            altInput: true,
            altFormat: "F j, Y h:i K", // Human-friendly display
            time_24hr: false, // For altFormat display
            minuteIncrement: 15,
            defaultDate: new Date(new Date().setHours(new Date().getHours() + 1, 0, 0, 0)),
            // Consider adding a placeholder if the field can be empty
            // static: true, // Useful if inside a modal or scrolling container
        });
        console.log("Flatpickr initialized for #event_date input.");
    } else {
        console.warn("Element with ID 'event_date' not found for Flatpickr.");
    }

    // --- Character Counter for Description ---
    const descriptionTextarea = document.getElementById('description');
    if (descriptionTextarea) {
        // Ensure the textarea has a maxlength attribute set by WTForms render_kw
        const maxLength = parseInt(descriptionTextarea.getAttribute('maxlength'), 10) || 5000;
        
        const counterElement = document.createElement('div');
        counterElement.className = 'text-xs text-gray-500 dark:text-gray-400 mt-1 text-right';
        
        const updateCounter = () => {
            const currentLength = descriptionTextarea.value.length;
            counterElement.textContent = `${currentLength} / ${maxLength}`;
            if (currentLength > maxLength) {
                counterElement.classList.add('text-red-500', 'dark:text-red-400'); // Added dark mode for error
                counterElement.classList.remove('text-gray-500', 'dark:text-gray-400');
            } else {
                counterElement.classList.remove('text-red-500', 'dark:text-red-400');
                counterElement.classList.add('text-gray-500', 'dark:text-gray-400');
            }
        };

        // Insert counter after the textarea
        // Ensure parentNode exists before trying to insert
        if (descriptionTextarea.parentNode) {
            descriptionTextarea.parentNode.insertBefore(counterElement, descriptionTextarea.nextSibling);
            
            updateCounter(); // Initial count
            descriptionTextarea.addEventListener('input', updateCounter);
            console.log("Character counter initialized for #description textarea.");
        } else {
            console.warn("Parent node for #description textarea not found. Counter not added.");
        }
    } else {
        console.warn("Element with ID 'description' not found for character counter.");
    }
});