/**
 * My Habit Tracker — Seamless Dynamic Engine (app.js)
 * Provides instantaneous, zero-reload user experience:
 * - 1-Click Task Check/Uncheck toggle with optimistic updates & stats recalculation.
 * - Dynamic Quick-Add task insertion into DOM with smooth entry animation.
 * - Soft-delete with slide-and-fade animation.
 * - Habit 7-day matrix check-off without reload.
 * - Assignment submission toggle with badge updates.
 * - Note pin/unpin and card deletion.
 * - Smart Assistant recommendation accept/dismiss cards.
 * - Single Page App (PJAX) instant navigation with top progress bar.
 * - Global Toast notifications.
 */

// ==========================================================================
// 1. Utilities & CSRF Extraction
// ==========================================================================
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function getCsrfToken(form = null) {
    if (form) {
        const input = form.querySelector('input[name="csrfmiddlewaretoken"]');
        if (input) return input.value;
    }
    return getCookie('csrftoken') || '';
}

// ==========================================================================
// 2. Toast Notification System
// ==========================================================================
function showToast(message, type = 'success', duration = 3000) {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'fixed bottom-6 right-6 z-50 flex flex-col space-y-2 pointer-events-none';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    const bgClasses = type === 'success' 
        ? 'bg-slate-900 text-white border border-slate-800 shadow-xl' 
        : type === 'error'
        ? 'bg-red-600 text-white shadow-xl'
        : 'bg-blue-600 text-white shadow-xl';

    const iconHtml = type === 'success' 
        ? `<svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 text-emerald-400 flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>`
        : type === 'error'
        ? `<svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 text-white flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>`
        : `<svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 text-blue-200 flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>`;

    toast.className = `flex items-center space-x-3 px-4 py-3 rounded-xl ${bgClasses} text-sm font-medium transform transition-all duration-300 translate-y-3 opacity-0 pointer-events-auto max-w-sm`;
    toast.innerHTML = `
        ${iconHtml}
        <span class="flex-1 text-xs leading-snug">${message}</span>
        <button class="text-slate-400 hover:text-white p-0.5 ml-2" onclick="this.parentElement.remove()">
            <svg xmlns="http://www.w3.org/2000/svg" class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
        </button>
    `;

    container.appendChild(toast);

    requestAnimationFrame(() => {
        toast.classList.remove('translate-y-3', 'opacity-0');
        toast.classList.add('translate-y-0', 'opacity-100');
    });

    setTimeout(() => {
        toast.classList.add('opacity-0', 'translate-y-2');
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

// ==========================================================================
// 3. Top Progress Bar for Seamless Navigations
// ==========================================================================
const TopLoader = {
    el: null,
    getEl() {
        if (!this.el) {
            this.el = document.getElementById('top-progress-bar');
            if (!this.el) {
                this.el = document.createElement('div');
                this.el.id = 'top-progress-bar';
                this.el.className = 'fixed top-0 left-0 h-[2.5px] bg-blue-600 transition-all duration-200 z-50 w-0 opacity-0 pointer-events-none shadow-sm shadow-blue-400';
                document.body.appendChild(this.el);
            }
        }
        return this.el;
    },
    start() {
        const el = this.getEl();
        el.style.transition = 'width 0.2s ease, opacity 0.1s ease';
        el.style.opacity = '1';
        el.style.width = '35%';
        setTimeout(() => {
            if (el.style.opacity === '1') el.style.width = '75%';
        }, 180);
    },
    done() {
        const el = this.getEl();
        el.style.width = '100%';
        setTimeout(() => {
            el.style.opacity = '0';
            setTimeout(() => { el.style.width = '0%'; }, 200);
        }, 150);
    }
};

// ==========================================================================
// 4. Interactive Action Handlers (Tasks, Habits, Assignments, Notes)
// ==========================================================================

// --- Task Check / Uncheck Toggle ---
async function handleTaskToggle(form, e) {
    if (e) e.preventDefault();
    const btn = form.querySelector('button[type="submit"]');
    const container = form.closest('.group') || form.closest('.rounded-xl');
    const titleSpan = container ? container.querySelector('span.text-sm, p.text-sm') : null;

    // Optimistic toggle
    const isCurrentlyChecked = btn && btn.classList.contains('bg-green-600');
    const newChecked = !isCurrentlyChecked;

