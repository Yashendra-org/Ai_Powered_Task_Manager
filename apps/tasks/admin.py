from django.contrib import admin
from .models import Category, Task, TaskHistory


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'color', 'created_at')
    list_filter = ('user',)
    search_fields = ('name',)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'category', 'priority', 'status', 'due_at', 'completed_at', 'deleted_at')
    list_filter = ('status', 'priority', 'category', 'user')
    search_fields = ('title', 'description')
    date_hierarchy = 'due_at'


@admin.register(TaskHistory)
class TaskHistoryAdmin(admin.ModelAdmin):
    list_display = ('task', 'action', 'previous_status', 'new_status', 'recorded_at')
    list_filter = ('action', 'recorded_at')
    search_fields = ('task__title', 'action')
