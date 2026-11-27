from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from .models import Assignment, Subject, Teacher
from .forms import AssignmentForm, SubjectForm, TeacherForm
from config.security import safe_redirect_back


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
    if subject_id and str(subject_id).isdigit():
        assignments = assignments.filter(subject_id=int(subject_id))
    else:
        subject_id = None

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
            assignment.save()
            messages.success(request, f"Assignment '{assignment.title}' created successfully!")
            return redirect('assignment_list')
    else:
        form = AssignmentForm(user=user)

    return render(request, 'assignments/form.html', {'form': form, 'title': 'Add College Assignment'})


@login_required
def assignment_edit_view(request, assignment_id):
    user = request.user
    assignment = get_object_or_404(Assignment, id=assignment_id, user=user)
    if request.method == 'POST':
        form = AssignmentForm(request.POST, request.FILES, instance=assignment, user=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Assignment updated successfully!")
            return redirect('assignment_list')
    else:
        form = AssignmentForm(instance=assignment, user=user)

    return render(request, 'assignments/form.html', {'form': form, 'assignment': assignment, 'title': 'Edit Assignment'})


@login_required
@require_POST
def assignment_delete_view(request, assignment_id):
    user = request.user
    assignment = get_object_or_404(Assignment, id=assignment_id, user=user)
    title = assignment.title
    assignment.delete()
    messages.info(request, f"Assignment '{title}' deleted.")
    return redirect('assignment_list')


@login_required
@require_POST
def assignment_submit_toggle_view(request, assignment_id):
    """
    1-Click toggle to mark an assignment as officially submitted.
    """
    user = request.user
    assignment = get_object_or_404(Assignment, id=assignment_id, user=user)
    if assignment.status == 'submitted':
        assignment.status = 'in_progress'
        assignment.submitted_at = None
        is_submitted = False
        msg = f"Assignment '{assignment.title}' marked as In Progress."
    else:
        assignment.status = 'submitted'
        assignment.submitted_at = timezone.now()
        is_submitted = True
        msg = f"Assignment '{assignment.title}' marked as Submitted! 🎉"

    assignment.save(update_fields=['status', 'submitted_at'])

    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', '')
    if is_ajax:
        return JsonResponse({
            'success': True,
            'assignment_id': str(assignment.id),
            'status': assignment.status,
            'is_submitted': is_submitted,
            'deadline_category': assignment.deadline_category,
            'message': msg,
        })

    if is_submitted:
        messages.success(request, msg)
    else:
        messages.info(request, msg)
    return safe_redirect_back(request, 'assignment_list')


@login_required
def subject_list_view(request):
    user = request.user
    subjects = Subject.objects.filter(user=user)

    if request.method == 'POST':
        form = SubjectForm(request.POST)
        if form.is_valid():
            subject = form.save(commit=False)
            subject.user = user
            subject.save()
            messages.success(request, f"Subject '{subject.name}' added successfully!")
            return redirect('subject_list')
    else:
        form = SubjectForm()

    return render(request, 'assignments/subject_list.html', {'subjects': subjects, 'form': form})


@login_required
@require_POST
def subject_delete_view(request, subject_id):
    user = request.user
    subject = get_object_or_404(Subject, id=subject_id, user=user)
    name = subject.name
    subject.delete()
    messages.info(request, f"Subject '{name}' deleted.")
    return redirect('subject_list')


@login_required
def teacher_list_view(request):
    user = request.user
    teachers = Teacher.objects.filter(user=user)

    if request.method == 'POST':
        form = TeacherForm(request.POST)
        if form.is_valid():
            teacher = form.save(commit=False)
            teacher.user = user
            teacher.save()
            messages.success(request, f"Teacher '{teacher.name}' added successfully!")
            return redirect('teacher_list')
    else:
        form = TeacherForm()

    return render(request, 'assignments/teacher_list.html', {'teachers': teachers, 'form': form})
