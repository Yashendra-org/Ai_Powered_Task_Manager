from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.db import connection
from apps.tasks.models import Task
from apps.assignments.models import Assignment
from apps.habits.models import Habit, HabitLog


@login_required
def dashboard_view(request):
    """
    Central Dashboard View (Module 1).
    Displays today's tasks, live metrics, upcoming assignments,
    habit status, and smart recommendations.
    """
    now = timezone.now()
    today = timezone.localdate()
    user = request.user
    
    # 1. Fetch user tasks for today
    today_tasks = Task.objects.active().filter(user=user, due_at__date=today)
    total_tasks_count = today_tasks.count()
    completed_tasks_count = today_tasks.filter(status='completed').count()
    pending_tasks_count = today_tasks.filter(status='pending').count()
    
    # Overdue tasks: active, not completed or cancelled, due before today
    overdue_tasks_count = Task.objects.active().filter(
        user=user,
        due_at__lt=now,
        status__in=['pending', 'in_progress']
    ).count()

    # Calculate completion rate
    if total_tasks_count > 0:
        completion_rate = round((completed_tasks_count / total_tasks_count) * 100, 1)
    else:
        completion_rate = 0.0

    # 2. Upcoming college assignments (next 7 days, unsubmitted)
    upcoming_assignments = Assignment.objects.filter(
        user=user
    ).exclude(status='submitted').order_by('due_at')[:4]

    # 3. Habits today
    user_habits = Habit.objects.filter(user=user, is_active=True)
    habits_today = []
    completed_habits_count = 0
    for h in user_habits:
        is_done = HabitLog.objects.filter(habit=h, date=today, status='completed').exists()
        if is_done:
            completed_habits_count += 1
        habits_today.append({
            'habit': h,
            'is_completed': is_done,
            'streak': h.current_streak(),
        })

    # Context for Dashboard
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
        'recommendations': [
            {
                'title': 'Foundation & Database Ready',
                'explanation': f'Phase 1 active. {total_tasks_count} tasks and {upcoming_assignments.count()} assignments tracked for today.',
                'type': 'system'
            }
        ]
    }
    return render(request, 'dashboard/index.html', context)


def get_greeting(hour):
    if hour < 12:
        return "Good morning"
    elif hour < 17:
        return "Good afternoon"
    else:
        return "Good evening"


def root_redirect(request):
    if request.user.is_authenticated:
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
        "Disallow: /dashboard/\n"
        "Disallow: /tasks/\n"
        "Disallow: /habits/\n"
        "Disallow: /assignments/\n"
        "Disallow: /notes/\n"
        "Disallow: /api/\n"
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
