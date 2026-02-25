/**
 * Admin Dashboard Logic
 * Handles sidebar toggles, clock, and other admin-specific UI interactions.
 */
document.addEventListener('DOMContentLoaded', () => {
    // --- Clock ---
    const clockEl = document.getElementById('clock');
    if (clockEl) {
        const updateClock = () => {
            const now = new Date();
            const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' };
            clockEl.innerText = now.toLocaleDateString('ar-SA', options);
        };
        setInterval(updateClock, 1000);
        updateClock();
    }

    // --- Sidebar Toggle for Mobile ---
    const sidebarToggleBtn = document.querySelector('.header-title .btn-light');
    if (sidebarToggleBtn) {
        sidebarToggleBtn.addEventListener('click', () => {
            document.getElementById('sidebar').classList.toggle('show');
        });
    }

    // --- Sidebar Accordion ---
    window.toggleMenu = function (id) {
        const el = document.getElementById(id);
        const btn = document.querySelector(`button[onclick="toggleMenu('${id}')"]`);

        // Close others (Optional - strict accordion)
        // document.querySelectorAll('.nav-sub-menu').forEach(item => {
        //     if (item.id !== id) item.classList.remove('open');
        // });

        // Toggle current
        el.classList.toggle('open');

        // Rotate chevron if we had one (we can add class later)
    };
});
