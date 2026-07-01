# Stage 3/5: Progressive implementation
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
            try:
                target_day = datetime.strptime(day_str, '%Y-%m-%d').date()
            except ValueError:
                target_day = today
        else:
            target_day = today

        start_date = target_day
        end_date = target_day
        period_title = target_day.strftime('%A, %d %B %Y')

        prev_url = f"?view=day&date={(target_day - timedelta(days=1)).strftime('%Y-%m-%d')}"
        next_url = f"?view=day&date={(target_day + timedelta(days=1)).strftime('%Y-%m-%d')}"

    elif view_mode == 'year':
        try:
            year = int(request.GET.get('year', today.year))
        except (ValueError, TypeError):
            year = today.year

        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)
        period_title = f"Year {year}"

        prev_url = f"?view=year&year={year - 1}"
        next_url = f"?view=year&year={year + 1}"

    else:  # custom
        start_str = request.GET.get('start_date')
        end_str = request.GET.get('end_date')
        try:
            start_date = datetime.strptime(start_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_str, '%Y-%m-%d').date()
            if start_date > end_date:
                start_date, end_date = end_date, start_date
        except (ValueError, TypeError):
            start_date = today - timedelta(days=14)
            end_date = today

        if (end_date - start_date).days > 60:
            end_date = start_date + timedelta(days=60)

        period_title = f"Custom: {start_date.strftime('%d %b')} – {end_date.strftime('%d %b %Y')}"
        prev_url = None
        next_url = None

    # Generate day columns list
    total_days = (end_date - start_date).days + 1
    days_list = []
    cur_day = start_date
    while cur_day <= end_date:
        days_list.append({
            'date': cur_day,
            'day_num': cur_day.day,
            'weekday_char': cur_day.strftime('%a')[0],  # S, M, T, W, T, F, S
            'weekday_short': cur_day.strftime('%a'),
            'month_short': cur_day.strftime('%b'),
            'date_str': cur_day.strftime('%Y-%m-%d'),
            'is_today': cur_day == today,
            'is_future': cur_day > today,
        })
        cur_day += timedelta(days=1)

    # Bulk query all habit logs in date range
    logs_qs = HabitLog.objects.filter(
        habit__in=habits,
        date__range=[start_date, end_date],
        status='completed'
    ).values('habit_id', 'date')

    logs_by_habit = defaultdict(set)
    daily_completed_counter = defaultdict(int)
    for item in logs_qs:
        h_id = item['habit_id']
        d = item['date']
        logs_by_habit[h_id].add(d)
        daily_completed_counter[d] += 1

    # Build per-habit row metrics
    habit_rows = []
    total_goals_sum = 0
    total_completed_sum = 0

    for h in habits:
        completed_dates = logs_by_habit[h.id]
        completed_in_period = len(completed_dates)

        if view_mode == 'month':
            goal = h.monthly_goal or 20
        elif view_mode == 'week':
            goal = max(1, round((h.monthly_goal or 20) * (7 / 30)))
        elif view_mode == 'day':
            goal = 1
        elif view_mode == 'year':
            goal = (h.monthly_goal or 20) * 12
        else:
            goal = max(1, round((h.monthly_goal or 20) * (total_days / 30)))

        progress_rate = min(100, round((completed_in_period / goal) * 100)) if goal > 0 else 0

        day_cells = []
        for d_info in days_list:
            is_done = d_info['date'] in completed_dates
            day_cells.append({
                'date_str': d_info['date_str'],
                'day_num': d_info['day_num'],
                'is_completed': is_done,
                'is_today': d_info['is_today'],
                'is_future': d_info['is_future'],
            })

        habit_rows.append({
            'habit': h,
            'color': h.assigned_color,
            'goal': goal,
            'completed_count': completed_in_period,
            'progress_rate': progress_rate,
            'streak': h.current_streak(),
            'days': day_cells,
        })

        total_goals_sum += goal
        total_completed_sum += completed_in_period

    # Daily mini-bars and chart trend data
    daily_totals = []
    chart_labels = []
    chart_data = []
    for d_info in days_list:
        cnt = daily_completed_counter[d_info['date']]
        daily_totals.append({
            'count': cnt,
            'is_today': d_info['is_today'],
            'day_num': d_info['day_num'],
        })
        chart_labels.append(str(d_info['day_num']))
        chart_data.append(cnt)

    # 3 Circular Progress Gauges (Matching screenshot)
    # 1. Period Progress Gauge (e.g. 61.9%)
    total_possible = len(habits) * total_days
    period_progress_pct = round((total_completed_sum / total_possible) * 100, 1) if total_possible > 0 else 0.0

    # 2. Normalized Elapsed Days Progress (e.g. 87.2%)
    elapsed_days = max(1, (min(today, end_date) - start_date).days + 1) if start_date <= today else 1
    normalized_possible = len(habits) * elapsed_days
    normalized_progress_pct = round((total_completed_sum / normalized_possible) * 100, 1) if normalized_possible > 0 else 0.0
    normalized_progress_pct = min(100.0, normalized_progress_pct)

    # 3. Momentum Progress (Last 3 Days Progress, e.g. 73.8%)
    momentum_start = max(start_date, today - timedelta(days=3))
    momentum_days = max(1, (today - momentum_start).days + 1)
    momentum_logs_count = sum(daily_completed_counter[momentum_start + timedelta(days=i)] for i in range(momentum_days))
    momentum_possible = len(habits) * momentum_days
    momentum_pct = round((momentum_logs_count / momentum_possible) * 100, 1) if momentum_possible > 0 else 0.0
    momentum_pct = min(100.0, momentum_pct)

    # Success rate badge calculation
    overall_success_rate = round((total_completed_sum / total_goals_sum) * 100) if total_goals_sum > 0 else 0
    if overall_success_rate >= 80:
        badge_label = "GOOD JOB ❤️"
    elif overall_success_rate >= 60:
        badge_label = "ON TRACK 🔥"
    elif overall_success_rate >= 40:
        badge_label = "BUILDING UP ⚡"
    else:
        badge_label = "GET STARTED 🎯"

    context = {
        'habits': habits,
