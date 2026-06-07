from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from apps.tasks.models import Task, TaskHistory
from apps.tasks.services import TaskService
from apps.assignments.models import Assignment
from .models import MLRecommendation
from .services import RecommendationEngine


@login_required
def end_of_day_review_view(request):
    """
    End-of-Day Review Workflow (Module 9).
    Generates daily performance recap and allows guided task rollover.
    """
    user = request.user
    today = timezone.localdate()

    # Generate or update DailySummary
    summary = RecommendationEngine.calculate_daily_summary(user, today)

    # Incomplete tasks for today
    unfinished_tasks = Task.objects.active().filter(
        user=user,
        due_at__date=today,
        status__in=['pending', 'in_progress']
    )

    # Upcoming assignment deadlines (next 48h)
    upcoming_assignments = Assignment.objects.filter(
        user=user,
        due_at__range=[timezone.now(), timezone.now() + timedelta(days=2)]
    ).exclude(status='submitted')

    context = {
        'summary': summary,
        'today_date': today.strftime('%A, %d %B %Y'),
        'unfinished_tasks': unfinished_tasks,
        'upcoming_assignments': upcoming_assignments,
    }
    return render(request, 'ml_engine/review.html', context)


@login_required
@require_POST
def apply_rollover_view(request):
    """
    Applies user-approved task rescheduling actions.
    Never reschedules tasks without explicit approval.
    """
    user = request.user
    tomorrow = timezone.now() + timedelta(days=1)
    
    # Process each task action
    task_ids = request.POST.getlist('task_ids')
