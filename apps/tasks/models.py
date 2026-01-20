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

