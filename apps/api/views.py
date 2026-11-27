from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import models
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny

from apps.tasks.models import Task, Category
from apps.habits.models import Habit, HabitLog
from apps.assignments.models import Assignment
from apps.notes.models import Note


class ApiRootView(APIView):
    """
    Public API Index / Discovery Endpoint.
    Lists available REST API resources and operational status.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({
            "success": True,
            "name": "My Habit Tracker REST API",
            "version": "v1",
            "status": "operational",
            "endpoints": {
                "tasks": request.build_absolute_uri('/api/v1/tasks/'),
                "habits": request.build_absolute_uri('/api/v1/habits/'),
                "assignments": request.build_absolute_uri('/api/v1/assignments/'),
                "analytics": request.build_absolute_uri('/api/v1/analytics/'),
            },
            "documentation": "See API.md for full request and response schemas."
        })


class TaskListCreateApiView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tasks = Task.objects.filter(user=request.user)
        status_param = request.query_params.get('status')
        if status_param:
            tasks = tasks.filter(status=status_param)
        priority_param = request.query_params.get('priority')
        if priority_param:
            tasks = tasks.filter(priority=priority_param)

        data = []
        for t in tasks:
            data.append({
                "id": str(t.id),
                "title": t.title,
                "description": t.description,
                "category": t.category.name if t.category else None,
                "priority": t.priority,
                "status": t.status,
                "estimated_duration": t.estimated_duration,
                "due_at": t.due_at.isoformat() if t.due_at else None,
                "completed_at": t.completed_at.isoformat() if t.completed_at else None,
            })

        return Response({
            "success": True,
            "data": {
                "count": len(data),
                "results": data
            }
        })

    def post(self, request):
        title = request.data.get('title')
        if not title or not str(title).strip():
            return Response({
                "success": False,
                "error": {
                    "code": "VALIDATION_FAILED",
                    "message": "The 'title' field is required."
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        clean_title = str(title).strip()[:255]
        clean_desc = str(request.data.get('description', ''))[:5000]
        
        # Priority validation (Vibe Coding Audit: Item 05 Strict Input Validation)
        priority = request.data.get('priority', 'medium')
        if priority not in ('low', 'medium', 'high'):
            priority = 'medium'

        # Estimated duration validation (Item 05 Negative Quantity Exploit defense)
        raw_duration = request.data.get('estimated_duration', 30)
        try:
            duration = int(raw_duration)
            if duration < 1 or duration > 1440:
                return Response({
                    "success": False,
                    "error": {
                        "code": "VALIDATION_FAILED",
                        "message": "The 'estimated_duration' must be between 1 and 1,440 minutes."
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
        except (ValueError, TypeError):
            duration = 30

        category = None
        category_id = request.data.get('category_id')
        if category_id and str(category_id).isdigit():
            category = Category.objects.filter(id=int(category_id), user=request.user).first()

        due_at_val = timezone.now() + timezone.timedelta(hours=4)
        raw_due_at = request.data.get('due_at')
        if raw_due_at:
            from django.utils.dateparse import parse_datetime
            parsed_dt = parse_datetime(str(raw_due_at))
            if not parsed_dt:
                return Response({
                    "success": False,
                    "error": {
                        "code": "VALIDATION_FAILED",
                        "message": "Invalid ISO-8601 datetime format for 'due_at'."
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
            if timezone.is_naive(parsed_dt):
                parsed_dt = timezone.make_aware(parsed_dt, timezone.get_current_timezone())
            due_at_val = parsed_dt

        task = Task.objects.create(
            user=request.user,
            title=clean_title,
            description=clean_desc,
            category=category,
            priority=priority,
            estimated_duration=duration,
            due_at=due_at_val,
        )


        return Response({
            "success": True,
            "data": {
                "id": str(task.id),
                "title": task.title,
                "status": task.status
            },
            "message": "Task created successfully."
        }, status=status.HTTP_201_CREATED)


class TaskToggleApiView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        task = get_object_or_404(Task, id=pk, user=request.user)
        if task.status == 'completed':
            task.status = 'pending'
            task.completed_at = None
        else:
            task.status = 'completed'
            task.completed_at = timezone.now()
        task.save()

        return Response({
            "success": True,
            "data": {
                "task_id": str(task.id),
                "status": task.status,
                "is_completed": task.status == 'completed'
            },
            "message": f"Task marked as {task.status}."
        })


class HabitListApiView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.localdate()
        habits = Habit.objects.filter(user=request.user, is_active=True).order_by('id')
        completed_today_ids = set(HabitLog.objects.filter(
            habit__in=habits,
            date=today,
            status='completed'
        ).values_list('habit_id', flat=True))

        data = []
        for h in habits:
            data.append({
                "id": h.id,
                "title": h.title,
                "frequency": h.frequency,
                "monthly_goal": h.monthly_goal,
                "color": h.color,
                "current_streak": h.current_streak(),
                "is_completed_today": h.id in completed_today_ids
            })

        return Response({
            "success": True,
            "data": data
        })


class AssignmentListApiView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        assignments = Assignment.objects.filter(user=request.user).select_related('subject')
        data = []
        for a in assignments:
            data.append({
                "id": str(a.id),
                "title": a.title,
                "subject": a.subject.name if a.subject else None,
                "subject_code": a.subject.code if a.subject else None,
                "due_at": a.due_at.isoformat() if a.due_at else None,
                "priority": a.priority,
                "status": a.status,
                "deadline_category": a.deadline_category
            })

        return Response({
            "success": True,
            "data": data
        })


class AnalyticsSummaryApiView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        tasks_total = Task.objects.filter(user=user).count()
        tasks_completed = Task.objects.filter(user=user, status='completed').count()
        habits_active = Habit.objects.filter(user=user, is_active=True).count()
        assignments_pending = Assignment.objects.filter(user=user).exclude(status='submitted').count()

        completion_rate = round((tasks_completed / tasks_total) * 100) if tasks_total > 0 else 0

        return Response({
            "success": True,
            "data": {
                "tasks_total": tasks_total,
                "tasks_completed": tasks_completed,
                "task_completion_rate": completion_rate,
                "habits_active": habits_active,
                "assignments_pending": assignments_pending,
            }
        })


class GlobalSearchApiView(APIView):
    """
    Pillar 5, #17: Global Omnibar & Command Palette Search API.
    Performs high-concurrence fuzzy search across Tasks, Habits, Assignments, and Notes.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.query_params.get('q', '').strip()[:100]
        if not query:
            return Response({
                "success": True,
                "data": {
                    "tasks": [],
                    "habits": [],
                    "assignments": [],
                    "notes": [],
                    "total_results": 0
                }
            })

        user = request.user

        # 1. Tasks search
        tasks = Task.objects.filter(user=user).filter(
            models.Q(title__icontains=query) | models.Q(description__icontains=query)
        ).select_related('category')[:8]

        tasks_data = [
            {
                "id": str(t.id),
                "title": t.title,
                "category": t.category.name if t.category else None,
                "priority": t.priority,
                "status": t.status,
                "due_at": t.due_at.strftime("%b %d, %H:%M") if t.due_at else None,
                "url": "/tasks/"
            }
            for t in tasks
        ]

        # 2. Habits search
        habits = Habit.objects.filter(user=user, is_active=True, title__icontains=query)[:5]
        habits_data = [
            {
                "id": h.id,
                "title": h.title,
                "frequency": h.frequency,
                "color": h.color,
                "url": "/habits/"
            }
            for h in habits
        ]

        # 3. Assignments search
        assignments = Assignment.objects.filter(user=user).filter(
            models.Q(title__icontains=query) | models.Q(subject__name__icontains=query)
        ).select_related('subject')[:5]

        assignments_data = [
            {
                "id": str(a.id),
                "title": a.title,
                "subject": a.subject.name if a.subject else None,
                "status": a.status,
                "url": "/assignments/"
            }
            for a in assignments
        ]

        # 4. Notes search
        notes = Note.objects.filter(user=user).filter(
            models.Q(title__icontains=query) | models.Q(content__icontains=query)
        )[:5]

        notes_data = [
            {
                "id": str(n.id),
                "title": n.title,
                "is_pinned": n.is_pinned,
                "url": "/notes/"
            }
            for n in notes
        ]

        total_count = len(tasks_data) + len(habits_data) + len(assignments_data) + len(notes_data)

        return Response({
            "success": True,
            "data": {
                "tasks": tasks_data,
                "habits": habits_data,
                "assignments": assignments_data,
                "notes": notes_data,
                "total_results": total_count
            }
        })

