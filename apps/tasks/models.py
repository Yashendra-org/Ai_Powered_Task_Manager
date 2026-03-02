import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


class Category(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=7, default='#2563EB', help_text="Hex color code")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tasks_category'
        verbose_name_plural = 'Categories'
        unique_together = ('user', 'name')
        ordering = ['name']

    def __str__(self):
        return self.name


class TaskQuerySet(models.QuerySet):
    def active(self):
        return self.filter(deleted_at__isnull=True)

    def deleted(self):
        return self.filter(deleted_at__isnull=False)

    def pending(self):
        return self.active().filter(status='pending')

    def completed(self):
        return self.active().filter(status='completed')

    def for_today(self, user):
        today = timezone.localdate()
        return self.active().filter(user=user, due_at__date=today)


class Task(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tasks')
    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.SET_NULL, related_name='tasks')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    
    scheduled_start = models.DateTimeField(null=True, blank=True)
    due_at = models.DateTimeField(null=True, blank=True)
    estimated_duration = models.PositiveIntegerField(default=30, help_text="Estimated minutes")
    actual_duration = models.PositiveIntegerField(null=True, blank=True, help_text="Actual minutes taken")
    
    is_recurring = models.BooleanField(default=False)
    recurrence_rule = models.CharField(max_length=50, blank=True, help_text="e.g. daily, weekly")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = TaskQuerySet.as_manager()

    class Meta:
        db_table = 'tasks_task'
        ordering = ['due_at', '-priority', 'created_at']

    def __str__(self):
        return self.title

    def soft_delete(self):
        self.deleted_at = timezone.now()
        self.save(update_fields=['deleted_at'])

    def restore(self):
        self.deleted_at = None
        self.save(update_fields=['deleted_at'])


class TaskHistory(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='history')
    previous_status = models.CharField(max_length=50)
    new_status = models.CharField(max_length=50)
    action = models.CharField(max_length=50, help_text="created, completed, postponed, rescheduled")
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tasks_task_history'
        verbose_name_plural = 'Task histories'
        ordering = ['-recorded_at']

    def __str__(self):
        return f"{self.task.title} -> {self.action} ({self.recorded_at})"
