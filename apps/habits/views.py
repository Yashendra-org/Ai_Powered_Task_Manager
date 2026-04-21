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
        'week_days': week_days,
        'total_habits': total_today,
        'completed_today': completed_today,
        'completion_rate': completion_rate,
        'start_of_week': start_of_week.strftime('%d %b'),
        'end_of_week': (start_of_week + timedelta(days=6)).strftime('%d %b %Y'),
    }
    return render(request, 'habits/list.html', context)


@login_required
def habit_create_view(request):
    user = request.user
    if request.method == 'POST':
        form = HabitForm(request.POST)
        if form.is_valid():
            habit = form.save(commit=False)
            habit.user = user
            habit.scheduled_days = form.cleaned_data['scheduled_days']
            habit.save()
            messages.success(request, f"Habit '{habit.title}' added to your tracker!")
            return redirect('habit_list')
    else:
        form = HabitForm()

    return render(request, 'habits/form.html', {'form': form, 'title': 'Create New Habit'})


@login_required
def habit_edit_view(request, habit_id):
    user = request.user
    habit = get_object_or_404(Habit, id=habit_id, user=user)
    if request.method == 'POST':
        form = HabitForm(request.POST, instance=habit)
        if form.is_valid():
            habit = form.save(commit=False)
            habit.scheduled_days = form.cleaned_data['scheduled_days']
            habit.save()
            messages.success(request, "Habit updated successfully!")
            return redirect('habit_list')
    else:
        form = HabitForm(instance=habit, initial={'scheduled_days': [str(d) for d in habit.scheduled_days]})

    return render(request, 'habits/form.html', {'form': form, 'habit': habit, 'title': 'Edit Habit'})


@login_required
@require_POST
def habit_delete_view(request, habit_id):
    user = request.user
    habit = get_object_or_404(Habit, id=habit_id, user=user)
    title = habit.title
    habit.delete()
    messages.info(request, f"Habit '{title}' removed.")
    return redirect('habit_list')


@login_required
@require_POST
def habit_toggle_log_view(request, habit_id):
    """
    1-Click daily check-off toggle for a habit.
    """
    user = request.user
    habit = get_object_or_404(Habit, id=habit_id, user=user)
    
    date_str = request.POST.get('date') or request.GET.get('date')
    if date_str:
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            target_date = timezone.localdate()
    else:
        target_date = timezone.localdate()

    log = HabitLog.objects.filter(habit=habit, date=target_date).first()
    if log and log.status == 'completed':
        log.delete()
        is_completed = False
        msg = f"Unchecked '{habit.title}' for {target_date.strftime('%a, %d %b')}."
    else:
        HabitLog.objects.update_or_create(
            habit=habit,
            date=target_date,
            defaults={'status': 'completed', 'completed_at': timezone.now()}
        )
        is_completed = True
        msg = f"Logged '{habit.title}' for {target_date.strftime('%a, %d %b')}! 🔥"

    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', '')
    if is_ajax:
        return JsonResponse({
            'success': True,
            'habit_id': str(habit.id),
            'date_str': target_date.strftime('%Y-%m-%d'),
            'is_completed': is_completed,
            'streak': habit.current_streak(),
            'message': msg,
        })

    if is_completed:
        messages.success(request, msg)
    else:
        messages.info(request, msg)
    return redirect(request.META.get('HTTP_REFERER', 'habit_list'))
