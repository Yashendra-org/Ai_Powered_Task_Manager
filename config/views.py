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
    
