from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Habit, HabitLog
from .forms import HabitForm


@login_required
def habit_list_view(request):
    """
    Weekly Habit Matrix & Consistency Tracker (Module 4).
    Displays habits alongside 7-day completion checkboxes and streaks.
    """
    user = request.user
    today = timezone.localdate()

    # Calculate Monday of current week
    start_of_week = today - timedelta(days=today.weekday())
    week_days = []
    for i in range(7):
        day_date = start_of_week + timedelta(days=i)
        week_days.append({
            'date': day_date,
            'name': day_date.strftime('%a'),
            'day_num': day_date.day,
            'is_today': day_date == today,
            'date_str': day_date.strftime('%Y-%m-%d'),
        })

    habits = Habit.objects.filter(user=user, is_active=True)
    habit_rows = []
    total_today = habits.count()
    completed_today = 0

    for habit in habits:
        # Get logs for this habit for the current week
        week_logs = set(
            HabitLog.objects.filter(
                habit=habit,
                date__range=[start_of_week, start_of_week + timedelta(days=6)],
                status='completed'
            ).values_list('date', flat=True)
        )

        day_statuses = []
        for day in week_days:
            is_done = day['date'] in week_logs
            if day['is_today'] and is_done:
                completed_today += 1
            day_statuses.append({
                'date_str': day['date_str'],
                'is_completed': is_done,
                'is_today': day['is_today'],
            })

        habit_rows.append({
            'habit': habit,
            'streak': habit.current_streak(),
            'days': day_statuses,
        })

    completion_rate = round((completed_today / total_today * 100), 1) if total_today > 0 else 0.0

    context = {
        'habit_rows': habit_rows,
