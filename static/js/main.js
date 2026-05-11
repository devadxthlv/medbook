/**
 * MedBook — main JavaScript
 *
 * Handles:
 * - Auto-dismiss flash messages after 5 seconds
 * - Active nav-link highlighting based on current URL
 */

document.addEventListener('DOMContentLoaded', function () {
    // ── Auto-dismiss alerts after 5 seconds ──
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            bsAlert.close();
        }, 5000);
    });

    // ── Highlight active navbar link ──
    const currentPath = window.location.pathname;
    document.querySelectorAll('.navbar .nav-link').forEach(function (link) {
        const href = link.getAttribute('href');
        if (href && href !== '/' && currentPath.startsWith(href)) {
            link.classList.add('active');
        } else if (href === '/' && currentPath === '/') {
            link.classList.add('active');
        }
    });
});
