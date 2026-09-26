/* Results — auto-recalculate grade preview when marks change */
document.addEventListener('DOMContentLoaded', () => {
    const marksInput = document.querySelector('input[name="marks"]');
    if (!marksInput) return;
    marksInput.addEventListener('input', (e) => {
        const v = parseFloat(e.target.value);
        if (isNaN(v)) return;
        // Simple preview hint
        let letter = 'F';
        if (v >= 90) letter = 'A+';
        else if (v >= 80) letter = 'A';
        else if (v >= 70) letter = 'B';
        else if (v >= 60) letter = 'C';
        else if (v >= 50) letter = 'D';
        let hint = document.getElementById('grade-hint');
        if (!hint) {
            hint = document.createElement('div');
            hint.id = 'grade-hint';
            hint.className = 'muted';
            e.target.parentNode.appendChild(hint);
        }
        hint.textContent = `Predicted grade: ${letter}`;
    });
});
