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
