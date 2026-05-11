from django.db import models
from django.conf import settings
from apps.tasks.models import Task
from apps.assignments.models import Assignment


class Reminder(models.Model):
    REMINDER_TYPE_CHOICES = [
        ('task_start', 'Task Start'),
        ('assignment_due', 'Assignment Due'),
        ('daily_review', 'Daily Review'),
