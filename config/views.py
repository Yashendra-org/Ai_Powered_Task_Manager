from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from apps.tasks.models import Task
from apps.assignments.models import Assignment
from apps.habits.models import Habit, HabitLog


@login_required
def dashboard_view(request):
    """
    Central Dashboard View (Module 1).
    Displays today's tasks, live metrics, upcoming assignments,
    habit status, and smart recommendations.
    """
    now = timezone.now()
    today = timezone.localdate()
    user = request.user
    
    # 1. Fetch user tasks for today
    today_tasks = Task.objects.active().filter(user=user, due_at__date=today)
    total_tasks_count = today_tasks.count()
    completed_tasks_count = today_tasks.filter(status='completed').count()
    pending_tasks_count = today_tasks.filter(status='pending').count()
    
    # Overdue tasks: active, not completed or cancelled, due before today
    overdue_tasks_count = Task.objects.active().filter(
        user=user,
        due_at__lt=now,
        status__in=['pending', 'in_progress']
    ).count()

    # Calculate completion rate
    if total_tasks_count > 0:
        completion_rate = round((completed_tasks_count / total_tasks_count) * 100, 1)
    else:
        completion_rate = 0.0

    # 2. Upcoming college assignments (next 7 days, unsubmitted)
    upcoming_assignments = Assignment.objects.filter(
        user=user
    ).exclude(status='submitted').order_by('due_at')[:4]

    # 3. Habits today
    user_habits = Habit.objects.filter(user=user, is_active=True)
    habits_today = []
    completed_habits_count = 0
    for h in user_habits:
        is_done = HabitLog.objects.filter(habit=h, date=today, status='completed').exists()
        if is_done:
            completed_habits_count += 1
        habits_today.append({
            'habit': h,
            'is_completed': is_done,
            'streak': h.current_streak(),
        })

    # Context for Dashboard
    context = {
        'current_date': now.strftime('%A, %d %B %Y'),
        'greeting': get_greeting(now.hour),
        'total_tasks_count': total_tasks_count,
        'completed_tasks_count': completed_tasks_count,
        'pending_tasks_count': pending_tasks_count,
        'overdue_tasks_count': overdue_tasks_count,
        'completion_rate': completion_rate,
        'today_tasks': today_tasks,
        'upcoming_assignments': upcoming_assignments,
        'habits_today': habits_today,
        'completed_habits_count': completed_habits_count,
        'total_habits_count': len(habits_today),
        'recommendations': [
            {
                'title': 'Foundation & Database Ready',
                'explanation': f'Phase 1 active. {total_tasks_count} tasks and {upcoming_assignments.count()} assignments tracked for today.',
                'type': 'system'
