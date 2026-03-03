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
            scheduled_start=scheduled_start,
            due_at=due_at or timezone.now(),
            estimated_duration=estimated_duration,
            status='pending',
        )
        TaskHistory.objects.create(
            task=task,
            previous_status='none',
            new_status='pending',
            action='created'
        )
        return task

    @staticmethod
    def toggle_completion(task):
        previous_status = task.status
        now = timezone.now()
        
        if task.status == 'completed':
            task.status = 'pending'
            task.completed_at = None
            action = 'marked_incomplete'
        else:
            task.status = 'completed'
            task.completed_at = now
            action = 'completed'

        task.save(update_fields=['status', 'completed_at', 'updated_at'])

        TaskHistory.objects.create(
            task=task,
            previous_status=previous_status,
            new_status=task.status,
            action=action
        )
        return task

    @staticmethod
    def soft_delete(task):
        previous_status = task.status
        task.soft_delete()
        TaskHistory.objects.create(
            task=task,
            previous_status=previous_status,
            new_status='deleted',
            action='soft_deleted'
        )
        return task

    @staticmethod
    def restore(task):
        task.restore()
        TaskHistory.objects.create(
            task=task,
            previous_status='deleted',
            new_status=task.status,
            action='restored'
        )
        return task

