/* Attendance — quick "mark all present" convenience button */
document.addEventListener('DOMContentLoaded', () => {
    const form = document.querySelector('form');
    if (!form) return;
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'btn btn-outline';
    btn.innerHTML = '<i class="bi bi-check2-all"></i> Mark all present';
    btn.style.marginRight = '8px';
    btn.addEventListener('click', () => {
        document.querySelectorAll('select[id^="id_student_"]').forEach(sel => {
            sel.value = 'present';
        });
    });
    form.insertBefore(btn, form.firstChild);
});
