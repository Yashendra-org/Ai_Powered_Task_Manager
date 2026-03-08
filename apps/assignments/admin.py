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
