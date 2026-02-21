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

