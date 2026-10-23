// Mobile Widget & Animation Stage 4/5
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

    if (btn) {
        btn.classList.add('animate-check-pop');
        setTimeout(() => btn.classList.remove('animate-check-pop'), 300);
        if (newChecked) {
            btn.className = "w-5 h-5 rounded-md border flex items-center justify-center transition-colors bg-green-600 border-green-600 text-white animate-check-pop";
            btn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" class="w-3.5 h-3.5 stroke-[3]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>`;
            if (titleSpan) {
                titleSpan.classList.add('line-through', 'text-slate-400');
                titleSpan.classList.remove('text-slate-900', 'text-slate-800');
            }
            if (container) container.classList.add('opacity-75');
        } else {
            btn.className = "w-5 h-5 rounded-md border flex items-center justify-center transition-colors border-slate-300 hover:border-blue-500 bg-white";
            btn.innerHTML = "";
            if (titleSpan) {
                titleSpan.classList.remove('line-through', 'text-slate-400');
                titleSpan.classList.add('text-slate-900');
            }
            if (container) container.classList.remove('opacity-75');
        }
    }

    try {
        const response = await fetch(form.action, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCsrfToken(form),
                'Accept': 'application/json',
            }
        });

        const data = await response.json();
        if (data.success) {
            // Update My Day stats badge if available
            const rateBadge = document.getElementById('my-day-completion-rate');
            if (rateBadge && data.today_total !== undefined) {
                rateBadge.textContent = `${data.today_completed} of ${data.today_total} Done (${data.today_rate}%)`;
            }

            // Update dashboard metric if present
            const completedMetric = document.querySelector('[data-metric="completed-tasks"]');
            if (completedMetric && data.today_completed !== undefined) {
                completedMetric.textContent = data.today_completed;
            }

            showToast(data.message || (newChecked ? "Task marked completed!" : "Task marked pending!"), 'success');
        }
    } catch (err) {
        console.error("Task toggle failed:", err);
        showToast("Error updating task. Please try again.", "error");
    }
}

// --- Quick Add Task to My Day ---
async function handleQuickAddTask(form, e) {
    if (e) e.preventDefault();
    const input = form.querySelector('input[type="text"]');
    if (!input || !input.value.trim()) return;

    const titleVal = input.value.trim();
    const submitBtn = form.querySelector('button[type="submit"]');
    if (submitBtn) submitBtn.disabled = true;

    try {
        const formData = new FormData(form);
        const response = await fetch(form.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCsrfToken(form),
                'Accept': 'application/json',
            }
        });

        const data = await response.json();
        if (data.success && data.task) {
            input.value = '';
            input.focus();

            // Insert new task card into DOM
            const listContainer = document.getElementById('task-list-container') || document.querySelector('.space-y-3');
            if (listContainer) {
                // Remove empty state placeholder if present
                const emptyNotice = listContainer.querySelector('.text-center');
                if (emptyNotice) emptyNotice.remove();

                const task = data.task;
                const taskCard = document.createElement('div');
                taskCard.className = "group p-4 bg-white border border-blue-200 rounded-xl hover:border-blue-300 hover:shadow-sm transition-all flex items-center justify-between transform -translate-y-2 opacity-0";
                
                const priorityBadgeClass = task.priority === 'high' 
                    ? 'bg-red-50 text-red-700 border-red-200' 
                    : task.priority === 'medium'
                    ? 'bg-amber-50 text-amber-700 border-amber-200'
                    : 'bg-slate-100 text-slate-700 border-slate-200';

                taskCard.innerHTML = `
                    <div class="flex items-center space-x-3.5 flex-1 min-w-0 mr-4">
                        <form method="POST" action="${task.toggle_url}" class="inline task-toggle-form">
                            <input type="hidden" name="csrfmiddlewaretoken" value="${getCsrfToken()}">
                            <button type="submit" class="w-5 h-5 rounded-md border flex items-center justify-center transition-colors border-slate-300 hover:border-blue-500 bg-white" title="Toggle Complete">
                            </button>
                        </form>
                        <div class="min-w-0 flex-1">
                            <div class="flex items-center space-x-2">
                                <span class="text-sm font-medium text-slate-900 group-hover:text-blue-600 transition-colors truncate">
                                    ${task.title}
                                </span>
                            </div>
                            <div class="flex items-center flex-wrap gap-2 text-xs text-slate-400 mt-1">
                                <span class="flex items-center">
                                    <svg xmlns="http://www.w3.org/2000/svg" class="w-3 h-3 mr-1" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
                                    ${task.estimated_duration}m
                                </span>
                            </div>
                        </div>
                    </div>
                    <div class="flex items-center space-x-3 flex-shrink-0">
                        <span class="text-[11px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border ${priorityBadgeClass}">
                            ${task.priority_display}
                        </span>
                        <a href="${task.edit_url}" class="opacity-0 group-hover:opacity-100 p-1.5 text-slate-400 hover:text-blue-600 rounded-lg hover:bg-slate-100 transition-all" title="Edit Task">
                            <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20h9"></path><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path></svg>
                        </a>
                        <form method="POST" action="${task.delete_url}" class="inline task-delete-form" onsubmit="return confirm('Move this task to Recently Deleted?');">
                            <input type="hidden" name="csrfmiddlewaretoken" value="${getCsrfToken()}">
                            <button type="submit" class="opacity-0 group-hover:opacity-100 p-1.5 text-slate-400 hover:text-red-600 rounded-lg hover:bg-red-50 transition-all" title="Delete Task">
                                <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                            </button>
                        </form>
                    </div>
                `;

                listContainer.prepend(taskCard);

                // Animate entry
                requestAnimationFrame(() => {
                    taskCard.style.transition = 'all 0.3s ease-out';
                    taskCard.classList.remove('-translate-y-2', 'opacity-0');
                    taskCard.classList.add('translate-y-0', 'opacity-100');
                });
            }

            // Update stats badge
            const rateBadge = document.getElementById('my-day-completion-rate');
            if (rateBadge && data.today_total !== undefined) {
                rateBadge.textContent = `${data.today_completed} of ${data.today_total} Done (${data.today_rate}%)`;
            }

            showToast(data.message, 'success');
        }
    } catch (err) {
        console.error("Quick add task error:", err);
        showToast("Error creating task. Please try again.", "error");
    } finally {
        if (submitBtn) submitBtn.disabled = false;
    }
}

// --- Task Soft Delete ---
async function handleTaskDelete(form, e) {
    if (e) e.preventDefault();
    if (!confirm("Move this task to Recently Deleted?")) return;

    const card = form.closest('.group') || form.closest('.rounded-xl');
    if (card) {
        card.style.transition = 'all 0.25s ease-out';
        card.style.opacity = '0';
        card.style.transform = 'scale(0.95)';
        card.style.maxHeight = '0px';
        card.style.paddingTop = '0';
        card.style.paddingBottom = '0';
        card.style.marginTop = '0';
        card.style.marginBottom = '0';
        card.style.overflow = 'hidden';
    }

    try {
        const response = await fetch(form.action, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCsrfToken(form),
                'Accept': 'application/json',
            }
        });

        const data = await response.json();
        if (data.success) {
            setTimeout(() => { if (card) card.remove(); }, 250);
            
            // Update stats badge
            const rateBadge = document.getElementById('my-day-completion-rate');
            if (rateBadge && data.today_total !== undefined) {
                rateBadge.textContent = `${data.today_completed} of ${data.today_total} Done (${data.today_rate}%)`;
            }

            showToast(data.message || "Task moved to Trash.", 'info');
        }
    } catch (err) {
        console.error("Task delete error:", err);
        if (card) card.style.opacity = '1';
        showToast("Error moving task to trash.", "error");
    }
}

// --- Habit 7-Day Matrix Toggle ---
async function handleHabitToggle(form, e) {
    if (e) e.preventDefault();
    const btn = form.querySelector('button[type="submit"]');
    const isCompleted = btn && btn.classList.contains('bg-emerald-600');
    const newStatus = !isCompleted;

    // Optimistic toggle
    if (btn) {
        btn.classList.add('animate-check-pop');
        setTimeout(() => btn.classList.remove('animate-check-pop'), 300);
        if (newStatus) {
            btn.className = "w-7 h-7 rounded-lg border flex items-center justify-center mx-auto transition-all bg-emerald-600 border-emerald-600 text-white shadow-sm shadow-emerald-200 animate-check-pop";
        } else {
            btn.className = "w-7 h-7 rounded-lg border flex items-center justify-center mx-auto transition-all border-slate-200 hover:border-emerald-400 bg-white text-transparent hover:text-slate-300";
        }
    }

    try {
        const formData = new FormData(form);
        const response = await fetch(form.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCsrfToken(form),
                'Accept': 'application/json',
            }
        });

        const data = await response.json();
        if (data.success) {
            // Update streak pill if returned
            const row = form.closest('tr');
            if (row && data.streak !== undefined) {
                const streakBadge = row.querySelector('td:nth-child(2) span');
                if (streakBadge) {
                    streakBadge.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" class="w-3.5 h-3.5 mr-1 text-emerald-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"></path></svg>${data.streak}d`;
                }
            }
            showToast(data.message, 'success');
        }
    } catch (err) {
        console.error("Habit toggle error:", err);
        showToast("Error updating habit log.", "error");
    }
}

// --- Assignment Submission Toggle ---
async function handleAssignmentToggle(form, e) {
    if (e) e.preventDefault();
    const btn = form.querySelector('button[type="submit"]');
    const card = form.closest('.rounded-2xl');
    const badge = card ? card.querySelector('span.rounded-full') : null;

    try {
        const response = await fetch(form.action, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCsrfToken(form),
                'Accept': 'application/json',
            }
        });

        const data = await response.json();
        if (data.success) {
            if (data.is_submitted) {
                if (btn) {
                    btn.textContent = "Mark In Progress";
                    btn.className = "px-2.5 py-1 text-xs font-semibold rounded-lg transition-colors bg-slate-100 text-slate-600 hover:bg-slate-200";
                }
                if (badge) {
                    badge.textContent = "Submitted";
                    badge.className = "text-[11px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-green-50 text-green-700 border border-green-200";
                }
                if (card) card.classList.add('opacity-80', 'bg-slate-50/50');
            } else {
                if (btn) {
                    btn.textContent = "Submit";
                    btn.className = "px-2.5 py-1 text-xs font-semibold rounded-lg transition-colors bg-green-50 text-green-700 hover:bg-green-100 border border-green-200";
                }
                if (badge) {
                    badge.textContent = "In Progress";
                    badge.className = "text-[11px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-amber-50 text-amber-700 border border-amber-200";
                }
                if (card) card.classList.remove('opacity-80', 'bg-slate-50/50');
            }
            showToast(data.message, 'success');
        }
    } catch (err) {
        console.error("Assignment toggle error:", err);
        showToast("Error updating assignment status.", "error");
    }
}

// --- Note Pin / Delete Toggle ---
async function handleNoteAction(form, e) {
    if (e) e.preventDefault();
    const isDelete = form.action.includes('/delete/');
    if (isDelete && !confirm("Delete this note?")) return;

    const card = form.closest('.rounded-2xl') || form.closest('.p-5');
    if (isDelete && card) {
        card.style.transition = 'all 0.25s ease-out';
        card.style.opacity = '0';
        card.style.transform = 'scale(0.95)';
    }

    try {
        const response = await fetch(form.action, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCsrfToken(form),
                'Accept': 'application/json',
            }
        });

        const data = await response.json();
        if (data.success) {
            if (isDelete && card) {
                setTimeout(() => card.remove(), 250);
            } else if (!isDelete && card) {
                // Pin toggle - reload partial view seamlessly
                loadPage(window.location.href, false);
            }
            showToast(data.message, 'info');
        }
    } catch (err) {
        console.error("Note action error:", err);
        showToast("Error processing note.", "error");
    }
}

// --- Recommendation Feedback (Accept / Dismiss) ---
async function handleRecommendationFeedback(form, e) {
    if (e) e.preventDefault();
    const card = form.closest('.rounded-2xl') || form.closest('.p-5');
    if (card) {
        card.style.transition = 'all 0.25s ease-out';
        card.style.opacity = '0';
        card.style.transform = 'scale(0.95)';
    }

    try {
        const response = await fetch(form.action, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCsrfToken(form),
                'Accept': 'application/json',
            }
        });

        const data = await response.json();
        if (data.success) {
            setTimeout(() => card.remove(), 250);
            showToast(data.message, 'success');
        }
    } catch (err) {
        console.error("Feedback error:", err);
        showToast("Error recording feedback.", "error");
    }
}

// ==========================================================================
// 5. Global Form Event Delegation
// ==========================================================================
document.addEventListener('submit', function (e) {
    const form = e.target;
    if (!form || !form.action) return;

    const action = form.action.toLowerCase();

    // 1. Task Toggle
    if (action.includes('/tasks/') && action.includes('/toggle/')) {
        handleTaskToggle(form, e);
        return;
    }

    // 2. Quick Add Task
    if (form.id === 'quick-add-task-form' || (action.includes('/tasks/today/') && form.method.toLowerCase() === 'post')) {
        handleQuickAddTask(form, e);
        return;
    }

    // 3. Task Delete
    if (action.includes('/tasks/') && action.includes('/delete/')) {
        handleTaskDelete(form, e);
        return;
    }

    // 4. Habit Toggle Log
    if (action.includes('/habits/') && action.includes('/log/')) {
        handleHabitToggle(form, e);
        return;
    }

    // 5. Assignment Submit Toggle
    if (action.includes('/assignments/') && action.includes('/submit-toggle/')) {
        handleAssignmentToggle(form, e);
        return;
    }

    // 6. Note Pin or Delete
    if (action.includes('/notes/') && (action.includes('/pin/') || action.includes('/delete/'))) {
        handleNoteAction(form, e);
        return;
    }

    // 7. Assistant Feedback
    if (action.includes('/assistant/feedback/')) {
        handleRecommendationFeedback(form, e);
        return;
    }
});

// ==========================================================================
// 6. Seamless SPA (PJAX) Page Router
// ==========================================================================
async function loadPage(url, pushState = true) {
    TopLoader.start();
    const mainEl = document.querySelector('main');

    try {
        const response = await fetch(url, {
            headers: {
                'X-PJAX': 'true',
            }
        });

        if (!response.ok) {
            window.location.href = url;
            return;
        }

        const html = await response.text();
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');

        const newMain = doc.querySelector('main');
        if (!newMain || !mainEl) {
            window.location.href = url;
            return;
        }

        // Fade transition
        mainEl.style.transition = 'opacity 0.12s ease-out';
        mainEl.style.opacity = '0';

        setTimeout(() => {
            mainEl.innerHTML = newMain.innerHTML;
            document.title = doc.title || document.title;

            // Execute any dynamic script tags inside newMain (e.g. Chart.js)
            const scripts = mainEl.querySelectorAll('script');
            scripts.forEach(s => {
                const newScript = document.createElement('script');
                if (s.src) newScript.src = s.src;
                else newScript.textContent = s.textContent;
                document.body.appendChild(newScript);
                newScript.remove();
            });

            // Re-render Lucide icons
            if (window.lucide) lucide.createIcons();

            // Update active state in sidebar navigation
            updateSidebarActiveLinks(url);
            initMobileNavigation();
            initMobileFab();

            mainEl.style.opacity = '1';
            TopLoader.done();

            if (pushState) {
                window.history.pushState({ url }, '', url);
            }
        }, 120);

    } catch (err) {
        console.error("PJAX load error:", err);
        TopLoader.done();
        window.location.href = url;
    }
}

function updateSidebarActiveLinks(currentUrl) {
    const sidebar = document.getElementById('sidebar');
    const currentPath = new URL(currentUrl, window.location.origin).pathname;

    if (sidebar) {
        const links = sidebar.querySelectorAll('nav a');
        links.forEach(link => {
            const linkPath = new URL(link.href, window.location.origin).pathname;
            const icon = link.querySelector('[data-lucide], i, svg');
            
            let isActive = false;
            if (linkPath === '/' && currentPath === '/') {
                isActive = true;
            } else if (linkPath !== '/' && currentPath.startsWith(linkPath)) {
                isActive = true;
            }

            if (isActive) {
                link.className = "flex items-center px-3 py-2.5 text-sm font-semibold rounded-lg bg-blue-50 text-blue-700 transition-colors";
                if (icon) {
                    icon.classList.remove('text-slate-400');
                    icon.classList.add('text-blue-600');
                }
            } else {
                link.className = "flex items-center px-3 py-2.5 text-sm font-medium rounded-lg text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition-colors";
                if (icon) {
                    icon.classList.remove('text-blue-600');
                    icon.classList.add('text-slate-400');
                }
            }
        });
    }

    // Update Mobile Bottom Nav Active Link
    const mobileNav = document.getElementById('mobileBottomNav');
    if (mobileNav) {
        const mobileLinks = mobileNav.querySelectorAll('a.mobile-nav-item');
        mobileLinks.forEach(link => {
            const linkPath = new URL(link.href, window.location.origin).pathname;
            let isActive = false;
            if (linkPath === '/' && currentPath === '/') {
                isActive = true;
            } else if (linkPath !== '/' && currentPath.startsWith(linkPath)) {
                isActive = true;
            }

            if (isActive) {
                link.className = "mobile-nav-item flex flex-col items-center justify-center flex-1 py-1 text-xs font-semibold text-blue-600 transition-colors";
            } else {
                link.className = "mobile-nav-item flex flex-col items-center justify-center flex-1 py-1 text-xs font-medium text-slate-500 hover:text-slate-900 transition-colors";
            }
        });
    }
}

// ==========================================================================
// 10. Mobile Drawer & Off-Canvas Controller
// ==========================================================================
function initMobileNavigation() {
    const sidebar = document.getElementById('sidebar');
    const backdrop = document.getElementById('sidebarBackdrop');
    const toggleBtn = document.getElementById('sidebarToggle');
    const closeBtn = document.getElementById('sidebarClose');
    const menuTrigger = document.getElementById('mobileMenuTrigger');

    function openSidebar() {
        if (!sidebar) return;
        sidebar.classList.remove('-translate-x-full');
        sidebar.classList.add('translate-x-0');
        if (backdrop) {
            backdrop.classList.remove('hidden');
        }
    }

    function closeSidebar() {
        if (!sidebar) return;
        sidebar.classList.remove('translate-x-0');
        sidebar.classList.add('-translate-x-full');
        if (backdrop) {
            backdrop.classList.add('hidden');
        }
    }

    if (toggleBtn) {
        toggleBtn.onclick = function (e) {
            e.stopPropagation();
            if (sidebar && sidebar.classList.contains('translate-x-0')) {
                closeSidebar();
            } else {
                openSidebar();
            }
        };
    }

    if (menuTrigger) {
        menuTrigger.onclick = function (e) {
            e.stopPropagation();
            if (sidebar && sidebar.classList.contains('translate-x-0')) {
                closeSidebar();
            } else {
                openSidebar();
            }
        };
    }

    if (closeBtn) {
        closeBtn.onclick = function (e) {
            e.stopPropagation();
            closeSidebar();
        };
    }

    if (backdrop) {
        backdrop.onclick = function () {
            closeSidebar();
        };
    }

    // Close on Escape key
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && sidebar && sidebar.classList.contains('translate-x-0')) {
            closeSidebar();
        }
    });

    // Close mobile drawer on link navigation
    if (sidebar) {
        sidebar.querySelectorAll('a').forEach(a => {
            a.addEventListener('click', function () {
                if (window.innerWidth < 768) {
                    closeSidebar();
                }
            });
        });
    }
}

// Intercept internal link navigation
document.addEventListener('click', function (e) {
    const link = e.target.closest('a');
    if (!link || !link.href) return;

    // Check if internal navigation link
    const targetUrl = new URL(link.href, window.location.origin);
    const isSameOrigin = targetUrl.origin === window.location.origin;

    if (!isSameOrigin) return;
    if (link.target === '_blank') return;
    if (link.hasAttribute('download')) return;
    if (link.getAttribute('href').startsWith('#')) return;
    if (targetUrl.pathname === '/logout/' || targetUrl.pathname === '/login/' || targetUrl.pathname === '/register/') return;
    if (targetUrl.pathname.startsWith('/admin/')) return;
    if (targetUrl.pathname.startsWith('/media/')) return;
    if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;

    e.preventDefault();
    loadPage(link.href, true);
});

// Handle browser Back / Forward buttons
window.addEventListener('popstate', function (e) {
    loadPage(window.location.href, false);
});

// ==========================================================================
// 11. Mobile Floating Action Button (FAB) Controller
// ==========================================================================
function initMobileFab() {
    const fabBtn = document.getElementById('mobileFabBtn');
    const fabMenu = document.getElementById('mobileFabMenu');
    const fabBackdrop = document.getElementById('mobileFabBackdrop');
    const fabIcon = document.getElementById('mobileFabIcon');

    if (!fabBtn || !fabMenu) return;

    let isOpen = false;

    function openFab() {
        isOpen = true;
        fabMenu.classList.remove('hidden');
        if (fabBackdrop) fabBackdrop.classList.remove('hidden');
        if (fabIcon) fabIcon.classList.add('rotate-45');
    }

    function closeFab() {
        isOpen = false;
        fabMenu.classList.add('hidden');
        if (fabBackdrop) fabBackdrop.classList.add('hidden');
        if (fabIcon) fabIcon.classList.remove('rotate-45');
    }

    fabBtn.onclick = function (e) {
        e.stopPropagation();
        if (isOpen) {
            closeFab();
        } else {
            openFab();
        }
    };

    if (fabBackdrop) {
        fabBackdrop.onclick = function () {
            closeFab();
        };
    }

    document.addEventListener('click', function (e) {
        if (isOpen && !e.target.closest('#mobileFabContainer')) {
            closeFab();
        }
    });

    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && isOpen) {
            closeFab();
        }
    });

    fabMenu.querySelectorAll('a').forEach(a => {
        a.addEventListener('click', function () {
            closeFab();
        });
    });
}

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', function () {
    if (window.lucide) lucide.createIcons();
    initMobileNavigation();
    initMobileFab();
});

