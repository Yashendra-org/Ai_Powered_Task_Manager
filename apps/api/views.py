# Stage 1/5: Implementation refinement
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
