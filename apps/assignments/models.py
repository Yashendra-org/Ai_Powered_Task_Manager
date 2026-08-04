import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


class Subject(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subjects')
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, blank=True, help_text="e.g. CS301, MATH202")

    class Meta:
        db_table = 'assignments_subject'
        unique_together = ('user', 'name')
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})" if self.code else self.name


class Teacher(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='teachers')
    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True)

    class Meta:
        db_table = 'assignments_teacher'
        ordering = ['name']

    def __str__(self):
        return self.name


class Assignment(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('submitted', 'Submitted'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='assignments')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='assignments')
    teacher = models.ForeignKey(Teacher, null=True, blank=True, on_delete=models.SET_NULL, related_name='assignments')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    assigned_date = models.DateField(default=timezone.localdate)
    due_at = models.DateTimeField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='high')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='not_started')
    submitted_at = models.DateTimeField(null=True, blank=True)
    attachment = models.FileField(upload_to='assignments/%Y/%m/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'assignments_assignment'
        ordering = ['due_at', '-priority']

    def __str__(self):
        return f"{self.title} - {self.subject.name}"

    @property
    def deadline_category(self):
        now = timezone.now()
        if self.due_at < now and self.status != 'submitted':
            return 'overdue'
        days_until_due = (timezone.localtime(self.due_at).date() - timezone.localdate()).days
        if days_until_due == 0:
            return 'due_today'
        elif days_until_due == 1:
            return 'due_tomorrow'
        elif 1 < days_until_due <= 3:
            return 'due_soon'
        else:
            return 'upcoming'
