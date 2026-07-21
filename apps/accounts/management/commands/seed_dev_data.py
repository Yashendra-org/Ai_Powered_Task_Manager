# Stage 2/5: Authentication & deployment refinement
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

        # 2. Categories
        cat_college, _ = Category.objects.get_or_create(user=user, name="College", defaults={"color": "#2563EB"})
        cat_coding, _ = Category.objects.get_or_create(user=user, name="Coding", defaults={"color": "#16A34A"})
        cat_personal, _ = Category.objects.get_or_create(user=user, name="Personal", defaults={"color": "#F59E0B"})

        # 3. Tasks for today
        now = timezone.now()
        today = timezone.localdate()

        t1, _ = Task.objects.get_or_create(
            user=user,
            title="Complete DSA practice — Graphs & Trees",
            defaults={
                "category": cat_coding,
                "priority": "high",
                "status": "completed",
                "due_at": now.replace(hour=18, minute=0),
                "estimated_duration": 60,
                "completed_at": now,
            }
        )

        t2, _ = Task.objects.get_or_create(
            user=user,
            title="Study Machine Learning — Supervised Algorithms",
            defaults={
                "category": cat_college,
