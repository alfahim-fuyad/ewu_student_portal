/* Students list interactions — confirm delete via row, highlight row hover */
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('table tbody tr').forEach(row => {
        row.style.cursor = 'pointer';
        row.addEventListener('click', (e) => {
            if (e.target.closest('a, button')) return;
            const link = row.querySelector('a[href]');
            if (link) window.location.href = link.href;
        });
    });
});
