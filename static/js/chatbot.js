/* =========================================================================
   Floating AI Chatbot — frontend logic
   ========================================================================= */

document.addEventListener('DOMContentLoaded', () => {
    const widget = document.getElementById('chatbotWidget');
    if (!widget) return;

    const fab = document.getElementById('chatbotFab');
    const windowEl = document.getElementById('chatbotWindow');
    const closeBtn = document.getElementById('chatbotClose');
    const clearBtn = document.getElementById('chatbotClear');
    const form = document.getElementById('chatbotForm');
    const input = document.getElementById('chatbotInput');
    const sendBtn = document.getElementById('chatbotSend');
    const body = document.getElementById('chatbotBody');

    // Toggle chat window open/closed
    fab.addEventListener('click', () => {
        const isHidden = windowEl.hasAttribute('hidden');
        if (isHidden) {
            windowEl.removeAttribute('hidden');
            input.focus();
            loadHistory();
        } else {
            windowEl.setAttribute('hidden', '');
        }
    });
    closeBtn.addEventListener('click', () => windowEl.setAttribute('hidden', ''));

    // Suggestion chips — click to send
    document.querySelectorAll('.chatbot-suggestions .chip').forEach(chip => {
        chip.addEventListener('click', () => {
            input.value = chip.dataset.q;
            form.requestSubmit();
        });
    });

    // Clear chat history
    if (clearBtn) {
        clearBtn.addEventListener('click', async () => {
            if (!confirm('Clear all chat history?')) return;
            try {
                const r = await fetch('/chatbot/clear/', { method: 'POST', headers: { 'X-CSRFToken': window.CSRF_TOKEN } });
                if (r.ok) {
                    body.innerHTML = '<div class="chat-welcome"><p>✨ Chat history cleared.</p></div>';
                }
            } catch (e) { console.error(e); }
        });
    }

    // Submit form
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const question = input.value.trim();
        if (!question) return;
        input.value = '';
        sendBtn.disabled = true;

        appendUser(question);
        const typing = appendTyping();

        try {
            const r = await fetch('/chatbot/chat/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': window.CSRF_TOKEN,
                },
                body: JSON.stringify({ question }),
            });
            const data = await r.json();
            typing.remove();
            if (data.error && !data.reply) {
                appendBot('⚠️ ' + (data.error || 'Unknown error'), false);
            } else {
                const allowed = data.allowed !== false;
                appendBot(data.reply, allowed);
            }
        } catch (err) {
            typing.remove();
            appendBot('🤖 Network error — please try again.', false);
            console.error(err);
        } finally {
            sendBtn.disabled = false;
            input.focus();
        }
    });

    // Load past history for resume
    async function loadHistory() {
        // If body already has welcome content, try to fetch history
        if (body.querySelector('.chat-welcome') === null) return; // already populated
        try {
            const r = await fetch('/chatbot/history/?limit=10');
            const data = await r.json();
            const rows = data.history || [];
            if (rows.length === 0) return;
            // Clear welcome and show history
            body.innerHTML = '';
            rows.forEach(row => {
                if (row.role === 'user') {
                    appendUser(row.content, false);
                } else {
                    appendBot(row.content, true, false);
                }
            });
        } catch (e) { /* swallow — keep welcome */ }
    }

    function appendUser(text, scroll = true) {
        const el = document.createElement('div');
        el.className = 'chat-msg user';
        el.innerHTML = `
            <div class="msg-avatar">👤</div>
            <div class="msg-bubble">${escapeHtml(text)}</div>
        `;
        body.appendChild(el);
        if (scroll) scrollToBottom();
    }

    function appendBot(text, allowed = true, scroll = true) {
        const el = document.createElement('div');
        el.className = 'chat-msg' + (allowed ? '' : ' denied');
        el.innerHTML = `
            <div class="msg-avatar">🤖</div>
            <div class="msg-bubble">${escapeHtml(text)}</div>
        `;
        body.appendChild(el);
        if (scroll) scrollToBottom();
    }

    function appendTyping() {
        const el = document.createElement('div');
        el.className = 'chat-typing';
        el.innerHTML = '<span></span><span></span><span></span>';
        body.appendChild(el);
        scrollToBottom();
        return el;
    }

    function scrollToBottom() {
        body.scrollTop = body.scrollHeight;
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = String(text || '');
        return div.innerHTML;
    }

    // Open with keyboard shortcut: Ctrl+Shift+A
    document.addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.shiftKey && (e.key === 'A' || e.key === 'a')) {
            e.preventDefault();
            fab.click();
        }
    });
});
