from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny

from apps.tasks.models import Task, Category
from apps.habits.models import Habit, HabitLog
from apps.assignments.models import Assignment


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

        category = None
        category_id = request.data.get('category_id')
        if category_id:
            category = Category.objects.filter(id=category_id, user=request.user).first()

        task = Task.objects.create(
            user=request.user,
            title=str(title).strip(),
            description=request.data.get('description', ''),
            category=category,
            priority=request.data.get('priority', 'medium'),
            estimated_duration=request.data.get('estimated_duration', 30),
            due_at=request.data.get('due_at') or (timezone.now() + timezone.timedelta(hours=4)),
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
