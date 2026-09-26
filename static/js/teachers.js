/* Teachers list interactions — same pattern as students.js */
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('table tbody tr').forEach(row => {
        row.addEventListener('click', (e) => {
            if (e.target.closest('a, button')) return;
            const link = row.querySelector('a[href]');
            if (link) window.location.href = link.href;
        });
    });
});
