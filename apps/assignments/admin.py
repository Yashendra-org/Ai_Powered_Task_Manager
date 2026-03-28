from django.contrib import admin
from .models import Subject, Teacher, Assignment


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'user')
    list_filter = ('user',)
    search_fields = ('name', 'code')


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'user')
    list_filter = ('user',)
    search_fields = ('name', 'email')


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'subject', 'user', 'due_at', 'priority', 'status', 'submitted_at')
    list_filter = ('status', 'priority', 'subject', 'user')
    search_fields = ('title', 'description')
    date_hierarchy = 'due_at'
