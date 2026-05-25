from django.db import models
from django.conf import settings
from apps.tasks.models import Task
from apps.assignments.models import Assignment


class Reminder(models.Model):
    REMINDER_TYPE_CHOICES = [
        ('task_start', 'Task Start'),
        ('assignment_due', 'Assignment Due'),
        ('daily_review', 'Daily Review'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reminders')
    task = models.ForeignKey(Task, null=True, blank=True, on_delete=models.CASCADE, related_name='reminders')
    assignment = models.ForeignKey(Assignment, null=True, blank=True, on_delete=models.CASCADE, related_name='reminders')
