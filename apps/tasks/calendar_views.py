import calendar
from datetime import datetime, date, timedelta
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import Task
from apps.assignments.models import Assignment
from apps.habits.models import HabitLog


@login_required
def calendar_view(request):
    """
    Unified Chronological Calendar (Module 5).
    Combines tasks, assignment deadlines, and habit logs in a monthly grid.
    """
    user = request.user
    today = timezone.localdate()

    # Get requested year and month, defaulting to current with strict bounds
    try:
        year = int(request.GET.get('year', today.year))
        month = int(request.GET.get('month', today.month))
    except (ValueError, TypeError):
        year = today.year
        month = today.month

    # Clamp month and year bounds to prevent OverflowError / DoS
    if month < 1:
        month = 12
        year -= 1
    elif month > 12:
        month = 1
        year += 1

    year = max(1970, min(2100, year))

    cal = calendar.Calendar(firstweekday=0) # Monday first
    month_days = cal.monthdatescalendar(year, month)

    start_date = month_days[0][0]
    end_date = month_days[-1][-1]

    # Pre-fetch user items for the visible date range
    tasks_range = Task.objects.active().filter(user=user, due_at__date__range=[start_date, end_date])
    assignments_range = Assignment.objects.filter(user=user, due_at__date__range=[start_date, end_date])
    habits_range = HabitLog.objects.filter(habit__user=user, date__range=[start_date, end_date], status='completed')

    # Group items by date
    tasks_by_date = {}
    for t in tasks_range:
        d = t.due_at.date()
        tasks_by_date.setdefault(d, []).append(t)

    assignments_by_date = {}
    for a in assignments_range:
        d = a.due_at.date()
        assignments_by_date.setdefault(d, []).append(a)

    habits_by_date = {}
    for h in habits_range:
        d = h.date
        habits_by_date.setdefault(d, []).append(h)

    # Build calendar grid structure
    weeks = []
    for week in month_days:
        days = []
        for day in week:
            days.append({
                'date': day,
                'day_num': day.day,
                'is_current_month': day.month == month,
                'is_today': day == today,
                'tasks': tasks_by_date.get(day, []),
                'assignments': assignments_by_date.get(day, []),
                'habits': habits_by_date.get(day, []),
            })
        weeks.append(days)

    month_name = calendar.month_name[month]

    # Prev / Next month links
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1

    context = {
        'weeks': weeks,
        'year': year,
        'month': month,
        'month_name': month_name,
        'prev_year': prev_year,
        'prev_month': prev_month,
        'next_year': next_year,
        'next_month': next_month,
    }
    return render(request, 'calendar/index.html', context)

