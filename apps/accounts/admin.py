from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("username", "email", "timezone", "daily_review_time", "is_staff", "is_active")
    list_filter = ("is_staff", "is_superuser", "is_active", "timezone")
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Productivity Preferences", {"fields": ("timezone", "daily_review_time")}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("Productivity Preferences", {"fields": ("email", "timezone", "daily_review_time")}),
    )
