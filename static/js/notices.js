/* Notices — confirm deletion */
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', (e) => {
            if (form.action.includes('/delete/')) {
                if (!confirm('Are you sure you want to delete this notice?')) {
                    e.preventDefault();
                }
            }
        });
    });
});
