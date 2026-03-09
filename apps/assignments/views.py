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
        assignments = assignments.filter(due_at__date__gt=today, due_at__date__lte=soon_limit).exclude(status='submitted')
    elif filter_type == 'overdue':
        assignments = assignments.filter(due_at__lt=now).exclude(status='submitted')
    elif filter_type == 'submitted':
        assignments = assignments.filter(status='submitted')
    elif filter_type == 'pending':
        assignments = assignments.exclude(status='submitted')

    # Subject filter
    subject_id = request.GET.get('subject')
    if subject_id:
        assignments = assignments.filter(subject_id=subject_id)

    assignments = assignments.order_by('due_at', '-priority')

    context = {
        'assignments': assignments,
        'subjects': subjects,
        'current_filter': filter_type,
        'current_subject': subject_id,
        'search_query': query,
        'total_count': Assignment.objects.filter(user=user).count(),
        'pending_count': Assignment.objects.filter(user=user).exclude(status='submitted').count(),
    }
    return render(request, 'assignments/list.html', context)


@login_required
def assignment_create_view(request):
    user = request.user
    # Ensure user has at least one subject
    if not Subject.objects.filter(user=user).exists():
        messages.info(request, "Please create at least one subject before adding an assignment.")
        return redirect('subject_list')

    if request.method == 'POST':
        form = AssignmentForm(request.POST, request.FILES, user=user)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.user = user
