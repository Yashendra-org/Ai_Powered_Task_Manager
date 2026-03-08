from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from .models import Task, Category
from .forms import TaskForm, QuickTaskForm, CategoryForm
from .services import TaskService


@login_required
def my_day_view(request):
    """
    Focus view for today's tasks (PRD Module 2).
    Includes sticky quick-add bar, priority chips, and 1-click completion.
    """
    user = request.user
    today = timezone.localdate()
    now = timezone.now()

    # Handle quick task creation form submission
    if request.method == 'POST':
        quick_form = QuickTaskForm(request.POST)
        if quick_form.is_valid():
            task = TaskService.create_task(
                user=user,
                title=quick_form.cleaned_data['title'],
                priority=quick_form.cleaned_data.get('priority') or 'medium',
                estimated_duration=quick_form.cleaned_data.get('estimated_duration') or 30,
                due_at=now,
            )
            is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', '')
            if is_ajax:
                today_tasks = Task.objects.active().filter(user=user, due_at__date=today)
                tot = today_tasks.count()
                comp = today_tasks.filter(status='completed').count()
                rate = round((comp / tot * 100), 1) if tot > 0 else 0.0
                return JsonResponse({
                    'success': True,
                    'message': f"Task '{task.title}' added to My Day!",
                    'task': {
                        'id': str(task.id),
                        'title': task.title,
                        'priority': task.priority,
                        'priority_display': task.get_priority_display(),
                        'estimated_duration': task.estimated_duration,
                        'category_name': task.category.name if task.category else None,
                        'status': task.status,
                        'is_completed': False,
                        'toggle_url': f'/tasks/{task.id}/toggle/',
                        'edit_url': f'/tasks/{task.id}/edit/',
                        'delete_url': f'/tasks/{task.id}/delete/',
                    },
                    'today_total': tot,
                    'today_completed': comp,
                    'today_rate': rate,
                })
            messages.success(request, "Task added to My Day!")
            return redirect('my_day')
        else:
            is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', '')
            if is_ajax:
                return JsonResponse({'success': False, 'errors': quick_form.errors}, status=400)
    else:
        quick_form = QuickTaskForm()

    tasks = Task.objects.active().filter(user=user, due_at__date=today).order_by('status', '-priority', 'due_at')
    categories = Category.objects.filter(user=user)

    total_count = tasks.count()
    completed_count = tasks.filter(status='completed').count()
    pending_count = tasks.filter(status='pending').count()
    completion_rate = round((completed_count / total_count * 100), 1) if total_count > 0 else 0.0

    context = {
        'tasks': tasks,
        'categories': categories,
        'quick_form': quick_form,
        'today_date': now.strftime('%A, %d %B'),
        'total_count': total_count,
        'completed_count': completed_count,
        'pending_count': pending_count,
        'completion_rate': completion_rate,
    }
    return render(request, 'tasks/my_day.html', context)


@login_required
def all_tasks_view(request):
    """
    Comprehensive task list with filters by status, priority, category and search.
    """
    user = request.user
    tasks = Task.objects.active().filter(user=user)
    categories = Category.objects.filter(user=user)

    # Search filter
    query = request.GET.get('q', '').strip()
    if query:
        tasks = tasks.filter(Q(title__icontains=query) | Q(description__icontains=query))

    # Status tab filter
    status_filter = request.GET.get('status', 'all')
    now = timezone.now()
    if status_filter == 'pending':
        tasks = tasks.filter(status='pending')
    elif status_filter == 'completed':
        tasks = tasks.filter(status='completed')
    elif status_filter == 'overdue':
        tasks = tasks.filter(due_at__lt=now, status__in=['pending', 'in_progress'])

    # Category filter
    category_id = request.GET.get('category')
    if category_id:
        tasks = tasks.filter(category_id=category_id)

    # Priority filter
    priority_filter = request.GET.get('priority')
    if priority_filter:
        tasks = tasks.filter(priority=priority_filter)

    tasks = tasks.order_by('status', '-priority', 'due_at')

    context = {
        'tasks': tasks,
        'categories': categories,
        'current_status': status_filter,
        'current_category': category_id,
        'current_priority': priority_filter,
        'search_query': query,
        'total_active': Task.objects.active().filter(user=user).count(),
    }
    return render(request, 'tasks/all_tasks.html', context)


@login_required
def task_create_view(request):
    user = request.user
    if request.method == 'POST':
        form = TaskForm(request.POST, user=user)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = user
            task.save()
            TaskService.create_task(
                user=user,
                title=task.title,
                description=task.description,
                category=task.category,
                priority=task.priority,
                scheduled_start=task.scheduled_start,
                due_at=task.due_at,
                estimated_duration=task.estimated_duration
            )
            messages.success(request, f"Task '{task.title}' created successfully!")
            return redirect('all_tasks')
    else:
        form = TaskForm(user=user)

    return render(request, 'tasks/task_form.html', {'form': form, 'title': 'Create New Task'})


@login_required
def task_edit_view(request, task_id):
    user = request.user
    task = get_object_or_404(Task.objects.active(), id=task_id, user=user)
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task, user=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Task updated successfully!")
            return redirect('all_tasks')
    else:
        form = TaskForm(instance=task, user=user)

    return render(request, 'tasks/task_form.html', {'form': form, 'task': task, 'title': 'Edit Task'})


@login_required
@require_POST
def task_toggle_complete_view(request, task_id):
    """
    Toggle task between pending and completed.
    Supports both AJAX and standard POST requests.
    """
    user = request.user
    task = get_object_or_404(Task.objects.active(), id=task_id, user=user)
    TaskService.toggle_completion(task)

    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', '')
    if is_ajax:
        today = timezone.localdate()
        today_tasks = Task.objects.active().filter(user=user, due_at__date=today)
        tot = today_tasks.count()
        comp = today_tasks.filter(status='completed').count()
        rate = round((comp / tot * 100), 1) if tot > 0 else 0.0

        return JsonResponse({
            'success': True,
            'task_id': str(task.id),
            'title': task.title,
            'status': task.status,
            'is_completed': task.status == 'completed',
            'today_total': tot,
            'today_completed': comp,
            'today_rate': rate,
            'message': f"Task '{task.title}' marked as {task.get_status_display().lower()}!",
        })

    messages.success(request, f"Task '{task.title}' marked as {task.get_status_display().lower()}!")
    return redirect(request.META.get('HTTP_REFERER', 'my_day'))


@login_required
@require_POST
def task_delete_view(request, task_id):
    """
    Soft delete a task, moving it to Recently Deleted.
    """
    user = request.user
    task = get_object_or_404(Task.objects.active(), id=task_id, user=user)
    TaskService.soft_delete(task)

    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', '')
    if is_ajax:
        today = timezone.localdate()
        today_tasks = Task.objects.active().filter(user=user, due_at__date=today)
        tot = today_tasks.count()
        comp = today_tasks.filter(status='completed').count()
        rate = round((comp / tot * 100), 1) if tot > 0 else 0.0
        return JsonResponse({
            'success': True,
            'task_id': str(task.id),
            'today_total': tot,
            'today_completed': comp,
            'today_rate': rate,
            'message': f"Task '{task.title}' moved to Trash.",
        })

    messages.info(request, f"Task moved to Trash. You can restore it anytime from Recently Deleted.")
    return redirect(request.META.get('HTTP_REFERER', 'all_tasks'))


@login_required
@require_POST
def task_restore_view(request, task_id):
    """
    Restore a soft-deleted task.
    """
    user = request.user
    task = get_object_or_404(Task.objects.deleted(), id=task_id, user=user)
    TaskService.restore(task)
    messages.success(request, f"Task '{task.title}' restored successfully!")
    return redirect('trash')


@login_required
@require_POST
def task_permanent_delete_view(request, task_id):
    """
    Permanently delete a task from the database.
    """
    user = request.user
    task = get_object_or_404(Task.objects.deleted(), id=task_id, user=user)
    title = task.title
    task.delete()
    messages.warning(request, f"Task '{title}' has been permanently deleted.")
    return redirect('trash')


@login_required
def trash_view(request):
    """
    View soft-deleted tasks with restore options.
    """
    user = request.user
    deleted_tasks = Task.objects.deleted().filter(user=user).order_by('-deleted_at')
    return render(request, 'tasks/trash.html', {'tasks': deleted_tasks})


@login_required
def category_create_view(request):
    user = request.user
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.user = user
            category.save()
            messages.success(request, f"Category '{category.name}' added!")
            return redirect('all_tasks')
    else:
        form = CategoryForm()

    return render(request, 'tasks/category_form.html', {'form': form})
