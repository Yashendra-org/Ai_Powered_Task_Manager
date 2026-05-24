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
