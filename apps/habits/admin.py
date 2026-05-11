from django.contrib import admin
from .models import Habit, HabitLog


@admin.register(Habit)
class HabitAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'frequency', 'target_time', 'is_active', 'created_at')
    list_filter = ('frequency', 'is_active', 'user')
    search_fields = ('title', 'description')


@admin.register(HabitLog)
class HabitLogAdmin(admin.ModelAdmin):
    list_display = ('habit', 'date', 'status', 'completed_at')
    list_filter = ('status', 'date')
    search_fields = ('habit__title',)
