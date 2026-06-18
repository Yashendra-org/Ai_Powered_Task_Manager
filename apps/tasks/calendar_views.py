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

    # Get requested year and month, defaulting to current
    year = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))

    # Clamp month bounds
    if month < 1:
        month = 12
        year -= 1
    elif month > 12:
        month = 1
        year += 1

    cal = calendar.Calendar(firstweekday=0) # Monday first
    month_days = cal.monthdatescalendar(year, month)

    start_date = month_days[0][0]
    end_date = month_days[-1][-1]

