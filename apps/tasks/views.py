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

