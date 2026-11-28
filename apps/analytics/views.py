import json
from datetime import timedelta
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from django.core.cache import cache
from apps.tasks.models import Task
from apps.habits.models import Habit, HabitLog


@login_required
def analytics_dashboard_view(request):
    """
    Productivity Analytics Engine (Module 8).
    Uses single-pass SQL GROUP BY aggregations and short-TTL distributed caching
    to sustain massive read concurrency without N+1 database queries.
    """
    user = request.user
    today = timezone.localdate()
    cache_key = f"analytics_view:v1:{user.id}:{today.isoformat()}"

    cached_context = cache.get(cache_key)
    if cached_context is not None:
        return render(request, 'analytics/dashboard.html', cached_context)

    start_day = today - timedelta(days=6)
    base_tasks = Task.objects.active().filter(user=user)

    # 1. 7-Day Completion Velocity in a single GROUP BY query
    daily_rows = (
        base_tasks.filter(due_at__date__gte=start_day, due_at__date__lte=today)
        .annotate(day=TruncDate('due_at'))
        .values('day')
        .annotate(
            planned=Count('id'),
            completed=Count('id', filter=Q(status='completed')),
        )
    )
    daily_map = {row['day']: row for row in daily_rows}

    velocity_labels = []
    completed_series = []
    planned_series = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        velocity_labels.append(d.strftime('%a, %d %b'))
        stats = daily_map.get(d)
        planned_series.append(stats['planned'] if stats else 0)
        completed_series.append(stats['completed'] if stats else 0)

    # 2. Category Distribution in a single GROUP BY query
    cat_rows = (
        base_tasks.values('category__name', 'category__color')
        .annotate(total=Count('id'))
        .order_by('-total')
    )
    category_labels = []
    category_counts = []
    category_colors = []
    for row in cat_rows:
        if row['total'] <= 0:
            continue
        category_labels.append(row['category__name'] or 'General')
        category_counts.append(row['total'])
        category_colors.append(row['category__color'] or ('#64748B' if not row['category__name'] else '#2563EB'))

    # 3. Overall Stats in a single aggregated query
    lifetime_agg = base_tasks.aggregate(
        total_lifetime=Count('id'),
        completed_lifetime=Count('id', filter=Q(status='completed')),
    )
    total_lifetime = lifetime_agg['total_lifetime'] or 0
    completed_lifetime = lifetime_agg['completed_lifetime'] or 0
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
        'velocity_labels': velocity_labels,
        'completed_series': completed_series,
        'planned_series': planned_series,
        'category_labels': category_labels,
        'category_counts': category_counts,
        'category_colors': category_colors,
        'velocity_labels_json': json.dumps(velocity_labels),
        'completed_series_json': json.dumps(completed_series),
        'planned_series_json': json.dumps(planned_series),
        'category_labels_json': json.dumps(category_labels),
        'category_counts_json': json.dumps(category_counts),
        'category_colors_json': json.dumps(category_colors),
    }
    cache.set(cache_key, context, timeout=45)
    return render(request, 'analytics/dashboard.html', context)
