# Stage 1/5: Authentication & deployment refinement
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import random

from apps.tasks.models import Category, Task
from apps.assignments.models import Subject, Teacher, Assignment
from apps.habits.models import Habit, HabitLog

User = get_user_model()


class Command(BaseCommand):
    help = "Seed initial development user and sample data for My Habit Tracker"

    def handle(self, *args, **options):
        # 1. Create or get test user
        user, created = User.objects.get_or_create(
            username="student",
            defaults={
                "email": "student@college.edu",
                "timezone": "Asia/Kolkata",
                "daily_review_time": "21:30:00",
                "is_staff": True,
                "is_superuser": True,
                "is_active": True,
            }
        )
        # Always guarantee password is set to password123 and account is active
        user.set_password("password123")
        user.is_active = True
        user.is_staff = True
        user.is_superuser = True
        user.save()
        self.stdout.write(self.style.SUCCESS("User 'student' (student@college.edu) active with password: password123"))
