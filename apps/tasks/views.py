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
