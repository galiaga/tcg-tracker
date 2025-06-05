const scrollToTopBtn = document.getElementById('scrollToTopBtn');
            const scrollThreshold = 200;
             if (scrollToTopBtn) {
                const toggleVisibility = () => {
                    if (window.scrollY > scrollThreshold) {
                        scrollToTopBtn.classList.remove('hidden');
                        scrollToTopBtn.classList.add('opacity-100');
                    } else {
                        scrollToTopBtn.classList.remove('opacity-100');
                        scrollToTopBtn.classList.add('hidden');
                    }
                };
                window.addEventListener('scroll', toggleVisibility, { passive: true });
                scrollToTopBtn.addEventListener('click', () => {
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                });
                toggleVisibility();
            }