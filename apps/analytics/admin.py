from django.contrib import admin
from .models import DailySummary


@admin.register(DailySummary)
class DailySummaryAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'total_tasks', 'completed_tasks', 'pending_tasks', 'overdue_tasks', 'completion_percentage', 'generated_at')
