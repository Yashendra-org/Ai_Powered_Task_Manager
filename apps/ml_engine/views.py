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
    
    # Process each task action with strict UUID validation
    import uuid
    raw_task_ids = request.POST.getlist('task_ids')
    valid_task_ids = []
    for tid in raw_task_ids[:100]:
        try:
            valid_task_ids.append(uuid.UUID(str(tid)))
        except (ValueError, TypeError):
            continue

    task_ids = valid_task_ids
    action = request.POST.get('action') # 'rollover_tomorrow' or 'cancel_tasks'

    if action == 'rollover_tomorrow':
        for tid in task_ids:
            task = Task.objects.active().filter(id=tid, user=user).first()
            if task:
                task.due_at = tomorrow
                task.save(update_fields=['due_at', 'updated_at'])
                TaskHistory.objects.create(
                    task=task,
                    previous_status=task.status,
                    new_status='pending',
                    action='rolled_over_to_tomorrow'
                )
        messages.success(request, f"{len(task_ids)} task(s) successfully rescheduled to tomorrow!")

    elif action == 'cancel_tasks':
        for tid in task_ids:
            task = Task.objects.active().filter(id=tid, user=user).first()
            if task:
                task.status = 'cancelled'
                task.save(update_fields=['status', 'updated_at'])
                TaskHistory.objects.create(
                    task=task,
                    previous_status='pending',
                    new_status='cancelled',
                    action='cancelled_during_review'
                )
        messages.info(request, f"{len(task_ids)} task(s) marked as cancelled.")

    return redirect('dashboard')


@login_required
def smart_assistant_view(request):
    """
    AI / ML Smart Assistant (Module 10).
    Displays routine detections, completion likelihood, and smart time tips.
    """
    user = request.user
    recommendations = RecommendationEngine.generate_recommendations(user)
    all_recommendations = MLRecommendation.objects.filter(user=user).order_by('-created_at')

    context = {
        'recommendations': all_recommendations.filter(status='pending'),
        'history': all_recommendations.exclude(status='pending')[:10],
    }
    return render(request, 'ml_engine/assistant.html', context)


@login_required
@require_POST
def recommendation_feedback_view(request, rec_id, action):
    user = request.user
    rec = get_object_or_404(MLRecommendation, id=rec_id, user=user)

    if action == 'accept':
        rec.status = 'accepted'
        rec.save(update_fields=['status'])

        # If it was a routine task suggestion, auto-create the task
        if rec.recommendation_type == 'routine_task':
            TaskService.create_task(
                user=user,
                title=rec.title.replace("Scheduled Routine: '", "").rstrip("'"),
                due_at=timezone.now(),
                priority='medium',
                estimated_duration=45
            )
            msg = "Accepted recommendation: Created task for today!"
        else:
            msg = "Recommendation accepted! Training feedback stored."

    elif action == 'reject':
        rec.status = 'rejected'
        rec.save(update_fields=['status'])
        msg = "Recommendation dismissed. Your feedback will refine future suggestions."
    else:
        msg = "Action recorded."

    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', '')
    if is_ajax:
        return JsonResponse({'success': True, 'rec_id': str(rec.id), 'action': action, 'message': msg})

    if action == 'accept':
        messages.success(request, msg)
    else:
        messages.info(request, msg)

    return redirect('smart_assistant')
