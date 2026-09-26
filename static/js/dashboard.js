/* Dashboard JS — animated stat counters (optional polish) */

document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.stat-value').forEach(el => {
        const text = el.textContent.trim();
        const num = parseFloat(text);
        if (isNaN(num)) return;
        const target = num;
        let current = 0;
        const step = target / 30;
        const timer = setInterval(() => {
            current += step;
            if (current >= target) {
                el.textContent = text; // restore original (preserves formatting)
                clearInterval(timer);
            } else {
                el.textContent = Math.floor(current);
            }
        }, 20);
    });
});
