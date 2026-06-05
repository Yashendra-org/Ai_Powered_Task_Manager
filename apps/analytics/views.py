import json
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from apps.tasks.models import Task, Category
from apps.assignments.models import Assignment
from apps.habits.models import Habit, HabitLog


@login_required
def analytics_dashboard_view(request):
    """
    Productivity Analytics Engine (Module 8).
    Delivers historical completion velocity, category breakdown,
    and habit consistency metrics visualized via Chart.js.
    """
    user = request.user
    today = timezone.localdate()

    # 1. 7-Day Completion Velocity
    velocity_labels = []
    completed_series = []
    planned_series = []

    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        velocity_labels.append(d.strftime('%a, %d %b'))

        day_tasks = Task.objects.active().filter(user=user, due_at__date=d)
        total_d = day_tasks.count()
        done_d = day_tasks.filter(status='completed').count()

        planned_series.append(total_d)
        completed_series.append(done_d)

    # 2. Category Distribution
    categories = Category.objects.filter(user=user)
    category_labels = []
    category_counts = []
    category_colors = []

    for cat in categories:
        cnt = Task.objects.active().filter(user=user, category=cat).count()
        if cnt > 0:
            category_labels.append(cat.name)
            category_counts.append(cnt)
            category_colors.append(cat.color or '#2563EB')

    # Add general uncategorized if any
    uncat_cnt = Task.objects.active().filter(user=user, category__isnull=True).count()
    if uncat_cnt > 0:
        category_labels.append("General")
        category_counts.append(uncat_cnt)
        category_colors.append("#64748B")

    # 3. Overall Stats
    all_tasks = Task.objects.active().filter(user=user)
    total_lifetime = all_tasks.count()
    completed_lifetime = all_tasks.filter(status='completed').count()
    overall_rate = round((completed_lifetime / total_lifetime * 100), 1) if total_lifetime > 0 else 0.0

    # 4. Habits Consistency
    total_habits = Habit.objects.filter(user=user, is_active=True).count()
    today_habits_done = HabitLog.objects.filter(habit__user=user, date=today, status='completed').count()

    context = {
        'total_lifetime': total_lifetime,
        'completed_lifetime': completed_lifetime,
        'overall_rate': overall_rate,
        'total_habits': total_habits,
        'today_habits_done': today_habits_done,
        'velocity_labels_json': json.dumps(velocity_labels),
        'completed_series_json': json.dumps(completed_series),
        'planned_series_json': json.dumps(planned_series),
        'category_labels_json': json.dumps(category_labels),
        'category_counts_json': json.dumps(category_counts),
        'category_colors_json': json.dumps(category_colors),
    }
    return render(request, 'analytics/dashboard.html', context)
