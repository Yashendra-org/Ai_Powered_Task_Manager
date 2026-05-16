import calendar
from datetime import datetime, date, timedelta
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import Task
from apps.assignments.models import Assignment
from apps.habits.models import HabitLog


@login_required
def calendar_view(request):
    """
    Unified Chronological Calendar (Module 5).
    Combines tasks, assignment deadlines, and habit logs in a monthly grid.
    """
    user = request.user
    today = timezone.localdate()
