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
