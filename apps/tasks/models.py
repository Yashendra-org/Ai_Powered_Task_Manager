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
