from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from .models import Assignment, Subject, Teacher
from .forms import AssignmentForm, SubjectForm, TeacherForm


@login_required
def assignment_list_view(request):
    """
    College Assignment Hub (Module 3).
    Filterable by status, urgency, subject, and keyword search.
    """
    user = request.user
    assignments = Assignment.objects.filter(user=user)
    subjects = Subject.objects.filter(user=user)

    # Search filter
    query = request.GET.get('q', '').strip()
    if query:
        assignments = assignments.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(subject__name__icontains=query) |
            Q(subject__code__icontains=query)
        )

    # Status / Urgency filter
    filter_type = request.GET.get('filter', 'all')
    now = timezone.now()
    today = timezone.localdate()

    if filter_type == 'due_today':
        assignments = assignments.filter(due_at__date=today).exclude(status='submitted')
    elif filter_type == 'due_soon':
        soon_limit = today + timezone.timedelta(days=3)
