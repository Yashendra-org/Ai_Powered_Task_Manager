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
    scheduled_at = models.DateTimeField()
    reminder_type = models.CharField(max_length=20, choices=REMINDER_TYPE_CHOICES)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'reminders_reminder'
        ordering = ['scheduled_at']

    def __str__(self):
        target = self.task.title if self.task else (self.assignment.title if self.assignment else 'General')
        return f"Reminder: {target} at {self.scheduled_at}"


class Notification(models.Model):
    NOTIFICATION_TYPE_CHOICES = [
        ('reminder', 'Reminder'),
        ('deadline', 'Deadline Alert'),
        ('system', 'System Message'),
        ('recommendation', 'AI Recommendation'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
