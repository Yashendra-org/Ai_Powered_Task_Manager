# Stage 1/5: Progressive implementation
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta, date
from collections import defaultdict
import calendar
import json
import csv

from .models import Habit, HabitLog
from .forms import HabitForm


@login_required
def habit_list_view(request):
    """
    Advanced Multi-Timeline Habit Tracker (Day / Week / Month / Year / Custom Timeline).
    Replicates the executive dashboard with:
    - Real-time line trend chart
    - Full-month 28-31 day matrix grid with color-coded checkmarks
    - Goal progress bars per habit
    - 3 Circular Donut Progress Gauges (Period, Normalized Elapsed, Momentum)
    - 1-Click Zero-Reload AJAX check-off
    """
    user = request.user
    today = timezone.localdate()

    # Timeline view mode: 'month' (default), 'week', 'day', 'year', 'custom'
    view_mode = request.GET.get('view', 'month').lower()
    if view_mode not in ['month', 'week', 'day', 'year', 'custom']:
        view_mode = 'month'

    habits = list(Habit.objects.filter(user=user, is_active=True).order_by('id'))

    # Curated palette for distinct habit color-coding (matching executive spreadsheet dashboard)
    default_palette = [
        '#10B981',  # Teal / Emerald
        '#3B82F6',  # Electric Blue
        '#8B5CF6',  # Purple
        '#F59E0B',  # Amber / Yellow
        '#EF4444',  # Red / Coral
        '#06B6D4',  # Cyan
        '#6366F1',  # Indigo
        '#F97316',  # Bright Orange
        '#14B8A6',  # Dark Teal
        '#EC4899',  # Pink / Magenta
    ]

    for i, h in enumerate(habits):
        if not h.color or h.color == '#10B981' or h.color == '#2563EB':
            h.assigned_color = default_palette[i % len(default_palette)]
        else:
            h.assigned_color = h.color

    # Determine timeline boundaries
    if view_mode == 'month':
        try:
            year = int(request.GET.get('year', today.year))
            month = int(request.GET.get('month', today.month))
        except (ValueError, TypeError):
            year = today.year
            month = today.month

        if month < 1:
            month = 12
            year -= 1
        elif month > 12:
            month = 1
            year += 1

        days_in_month = calendar.monthrange(year, month)[1]
        start_date = date(year, month, 1)
        end_date = date(year, month, days_in_month)
        period_title = f"{start_date.strftime('%B %Y')}"

        prev_month = month - 1 if month > 1 else 12
        prev_year = year if month > 1 else year - 1
        next_month = month + 1 if month < 12 else 1
        next_year = year if month < 12 else year + 1

        prev_url = f"?view=month&year={prev_year}&month={prev_month}"
        next_url = f"?view=month&year={next_year}&month={next_month}"

    elif view_mode == 'week':
        ref_date_str = request.GET.get('date')
        if ref_date_str:
            try:
                ref_date = datetime.strptime(ref_date_str, '%Y-%m-%d').date()
            except ValueError:
                ref_date = today
        else:
            ref_date = today

        start_date = ref_date - timedelta(days=ref_date.weekday())  # Monday
        end_date = start_date + timedelta(days=6)                    # Sunday
        period_title = f"Week: {start_date.strftime('%d %b')} – {end_date.strftime('%d %b %Y')}"

        prev_url = f"?view=week&date={(start_date - timedelta(days=7)).strftime('%Y-%m-%d')}"
        next_url = f"?view=week&date={(start_date + timedelta(days=7)).strftime('%Y-%m-%d')}"

    elif view_mode == 'day':
        day_str = request.GET.get('date')
        if day_str:
