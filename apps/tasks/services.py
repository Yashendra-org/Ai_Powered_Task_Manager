from django.utils import timezone
from .models import Task, TaskHistory


class TaskService:
    @staticmethod
    def create_task(user, title, description='', category=None, priority='medium',
                    scheduled_start=None, due_at=None, estimated_duration=30):
        task = Task.objects.create(
            user=user,
            title=title,
            description=description,
            category=category,
            priority=priority,
