from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.db import connection
from django.db.models import Count, Q
from django.core.cache import cache
from apps.tasks.models import Task
from apps.assignments.models import Assignment
from apps.habits.models import Habit, HabitLog


@login_required
def dashboard_view(request):
    """
    Central Dashboard View (Module 1).
    Uses single-query SQL aggregation and batched habit streak lookup
    to eliminate N+1 database round-trips at high concurrency.
    """
    now = timezone.now()
    today = timezone.localdate()
    user = request.user

    # 1. Aggregated task counts in a single DB query + today task list slice
    task_stats = Task.objects.active().filter(user=user).aggregate(
        total_today=Count('id', filter=Q(due_at__date=today)),
        completed_today=Count('id', filter=Q(due_at__date=today, status='completed')),
        pending_today=Count('id', filter=Q(due_at__date=today, status='pending')),
        overdue=Count('id', filter=Q(due_at__lt=now, status__in=['pending', 'in_progress'])),
    )
    total_tasks_count = task_stats['total_today'] or 0
    completed_tasks_count = task_stats['completed_today'] or 0
    pending_tasks_count = task_stats['pending_today'] or 0
    overdue_tasks_count = task_stats['overdue'] or 0

    today_tasks = Task.objects.active().filter(
        user=user, due_at__date=today
    ).select_related('category').order_by('status', '-priority', 'due_at')[:50]

    completion_rate = round((completed_tasks_count / total_tasks_count) * 100, 1) if total_tasks_count > 0 else 0.0

    # 2. Upcoming college assignments (prefetched subject, evaluated once)
    upcoming_assignments = list(
        Assignment.objects.filter(user=user)
        .exclude(status='submitted')
        .select_related('subject')
        .order_by('due_at')[:4]
    )

    # 3. Habits today (batched 1-query streak + completion lookup)
    user_habits = list(Habit.objects.filter(user=user, is_active=True).order_by('title'))
    streaks_map, completed_today_ids = Habit.compute_streaks_for_habits(user_habits, today=today)
    habits_today = []
    for h in user_habits:
        habits_today.append({
            'habit': h,
            'is_completed': h.id in completed_today_ids,
            'streak': streaks_map.get(h.id, 0),
        })
    completed_habits_count = len(completed_today_ids)

    all_recommendations = [
        {
            'id': 'system_foundation',
            'title': 'Foundation & Database Ready',
            'explanation': f'Phase 1 active. {total_tasks_count} tasks and {len(upcoming_assignments)} assignments tracked for today.',
            'type': 'system'
        }
    ]
    dismissed_ids = set(request.session.get('dismissed_insights', []))
    recommendations = [rec for rec in all_recommendations if rec['id'] not in dismissed_ids]

    context = {
        'current_date': now.strftime('%A, %d %B %Y'),
        'greeting': get_greeting(now.hour),
        'total_tasks_count': total_tasks_count,
        'completed_tasks_count': completed_tasks_count,
        'pending_tasks_count': pending_tasks_count,
        'overdue_tasks_count': overdue_tasks_count,
        'completion_rate': completion_rate,
        'today_tasks': today_tasks,
        'upcoming_assignments': upcoming_assignments,
        'habits_today': habits_today,
        'completed_habits_count': completed_habits_count,
        'total_habits_count': len(habits_today),
        'recommendations': recommendations,
    }
    return render(request, 'dashboard/index.html', context)


@login_required
@require_POST
def dismiss_dashboard_insight_view(request):
    """Persistently dismisses a dashboard insight card in the user's session."""
    insight_id = (request.POST.get('insight_id') or '').strip()[:64]
    if insight_id:
        dismissed = list(request.session.get('dismissed_insights', []))
        if insight_id not in dismissed:
            dismissed.append(insight_id)
            request.session['dismissed_insights'] = dismissed[-25:]
            request.session.modified = True

    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', '')
    if is_ajax:
        return JsonResponse({'success': True, 'dismissed_id': insight_id})
    return redirect('dashboard')


def get_greeting(hour):
    if hour < 12:
        return "Good morning"
    elif hour < 17:
        return "Good afternoon"
    else:
        return "Good evening"


def root_redirect(request):
    if request.user.is_authenticated:
        landing = getattr(request.user, 'default_landing_view', 'dashboard')
        if landing == 'my_day':
            return redirect('my_day')
        elif landing == 'all_tasks':
            return redirect('all_tasks')
        elif landing == 'analytics':
            return redirect('analytics_dashboard')
        return redirect('dashboard')
    return redirect('login')


def health_check_view(request):
    """
    103 Things Guide (#38): Lightweight health check endpoint.
    Verifies application and database connectivity for container orchestrators and uptime monitors.
    """
    db_ok = False
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            db_ok = cursor.fetchone() == (1,)
    except Exception:
        db_ok = False

    status_code = 200 if db_ok else 503
    return JsonResponse({
        "status": "healthy" if db_ok else "unhealthy",
        "database": "connected" if db_ok else "disconnected",
        "timestamp": timezone.now().isoformat(),
        "service": "ai-task-manager"
    }, status=status_code)


def robots_txt_view(request):
    """
    103 Things Guide (#90) & Security Guide: Protect private user routes from crawler indexing.
    """
    domain = request.get_host()
    scheme = "https" if request.is_secure() else "http"
    content = (
        "User-agent: *\n"
        "Allow: /$\n"
        "Allow: /login/\n"
        "Allow: /register/\n"
        "Allow: /auth/\n"
        "Disallow: /dashboard/\n"
        "Disallow: /account/\n"
        "Disallow: /tasks/\n"
        "Disallow: /habits/\n"
        "Disallow: /assignments/\n"
        "Disallow: /notes/\n"
        "Disallow: /analytics/\n"
        "Disallow: /ai/\n"
        "Disallow: /api/\n"
        "Disallow: /notifications/\n"
        "Disallow: /calendar/\n"
        "Disallow: /secure-admin/\n"
        "Disallow: /admin/\n\n"
        f"Sitemap: {scheme}://{domain}/sitemap.xml\n"
    )
    return HttpResponse(content, content_type="text/plain; charset=utf-8")


def sitemap_xml_view(request):
    """
    103 Things Guide (#90) & Publishing Guide: Standard sitemap.xml for public page discovery.
    """
    domain = request.get_host()
    scheme = "https" if request.is_secure() else "http"
    base_url = f"{scheme}://{domain}"
    today = timezone.localdate().isoformat()
    content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>{base_url}/</loc>
        <lastmod>{today}</lastmod>
        <changefreq>daily</changefreq>
        <priority>1.0</priority>
    </url>
    <url>
        <loc>{base_url}/auth/login/</loc>
        <lastmod>{today}</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.9</priority>
    </url>
    <url>
        <loc>{base_url}/auth/register/</loc>
        <lastmod>{today}</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.9</priority>
    </url>
    <url>
        <loc>{base_url}/login/</loc>
        <lastmod>{today}</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.8</priority>
    </url>
    <url>
        <loc>{base_url}/register/</loc>
        <lastmod>{today}</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.8</priority>
    </url>
</urlset>"""
    return HttpResponse(content.strip(), content_type="application/xml; charset=utf-8")


def custom_page_not_found_view(request, exception=None):
    """
    UI/UX State 05 & 103 Things Guide (#40): Friendly custom 404 Error State.
    """
    return render(request, '404.html', status=404)


def custom_server_error_view(request):
    """
    UI/UX State 05 & 103 Things Guide (#40): Friendly custom 500 Server Error State.
    """
    return render(request, '500.html', status=500)


def offline_view(request):
    """
    PWA Offline Fallback View (Pillar 5, #18).
    Rendered when client is offline or by Service Worker navigation fallback.
    """
    return render(request, 'offline.html')

