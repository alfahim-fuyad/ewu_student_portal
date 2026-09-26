/* Base site JavaScript — sidebar toggle, active-link highlight */

document.addEventListener('DOMContentLoaded', () => {
    // Sidebar toggle for desktop collapse + mobile slide
    const toggleBtn = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('appSidebar');

    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener('click', () => {
            if (window.innerWidth <= 1024) {
                sidebar.classList.toggle('open');
                toggleBackdrop();
            } else {
                sidebar.classList.toggle('collapsed');
            }
        });
    }

    function toggleBackdrop() {
        let bd = document.querySelector('.sidebar-backdrop');
        if (!bd) {
            bd = document.createElement('div');
            bd.className = 'sidebar-backdrop';
            document.body.appendChild(bd);
            bd.addEventListener('click', () => {
                sidebar.classList.remove('open');
                bd.classList.remove('show');
            });
        }
        bd.classList.toggle('show');
    }

    // Highlight active sidebar link based on current URL path
    const currentPath = window.location.pathname;
    document.querySelectorAll('.sidebar .nav-link').forEach(link => {
        const href = link.getAttribute('href');
        if (!href) return;
        if (currentPath === href || currentPath.startsWith(href + '/')) {
            link.classList.add('active');
        }
    });

    // Auto-close flash messages after 5 seconds
    document.querySelectorAll('.alert').forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.4s';
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 400);
        }, 5000);
    });
});
