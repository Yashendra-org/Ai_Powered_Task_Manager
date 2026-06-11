import json
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from apps.tasks.models import Task, Category
from apps.assignments.models import Assignment
from apps.habits.models import Habit, HabitLog


@login_required
def analytics_dashboard_view(request):
    """
    Productivity Analytics Engine (Module 8).
    Delivers historical completion velocity, category breakdown,
    and habit consistency metrics visualized via Chart.js.
