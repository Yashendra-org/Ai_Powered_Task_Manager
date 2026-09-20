# Stage 3/5: Admin account provisioning
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

        # 1b. Create or update administrator superuser
        admin_user, _ = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@myhabittracker.com",
                "timezone": "Asia/Kolkata",
                "is_staff": True,
                "is_superuser": True,
                "is_active": True,
            }
        )
        admin_user.set_password("admin123")
        admin_user.is_active = True
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.save()
        self.stdout.write(self.style.SUCCESS("Admin user 'admin' active with password: admin123 (Superuser)"))

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
                "priority": "high",
                "status": "pending",
                "due_at": now.replace(hour=20, minute=0),
                "estimated_duration": 45,
            }
        )

        t3, _ = Task.objects.get_or_create(
            user=user,
            title="Revise DBMS Normalization notes",
            defaults={
                "category": cat_college,
                "priority": "medium",
                "status": "pending",
                "due_at": now.replace(hour=21, minute=0),
                "estimated_duration": 30,
            }
        )

        # 4. Subjects & Assignments
        subject_dbms, _ = Subject.objects.get_or_create(user=user, name="Database Management Systems", defaults={"code": "CS302"})
        teacher_sharma, _ = Teacher.objects.get_or_create(user=user, name="Dr. R. Sharma", defaults={"email": "sharma@college.edu"})

        Assignment.objects.get_or_create(
            user=user,
            title="DBMS Assignment 3: B+ Trees & Indexing",
            subject=subject_dbms,
            defaults={
                "teacher": teacher_sharma,
                "description": "Solve exercise problems 1 to 10 on B+ Trees indexing.",
                "assigned_date": today,
                "due_at": now + timezone.timedelta(days=2),
                "priority": "high",
                "status": "in_progress",
            }
        )

        # 5. Habits (11 Habits matching Executive Dashboard)
        habits_catalog = [
            ("Stretch or do yoga", 5, "#10B981"),
            ("Walk 10,000 steps", 7, "#0EA5E9"),
            ("Read a book chapter", 15, "#6366F1"),
            ("Declutter a space", 4, "#F59E0B"),
            ("Floss teeth & skincare", 20, "#EF4444"),
            ("Play a guitar", 10, "#10B981"),
            ("Call family", 10, "#06B6D4"),
            ("Volunteer", 3, "#8B5CF6"),
            ("Put $10 to savings", 10, "#F59E0B"),
            ("Daily DSA Practice", 25, "#10B981"),
            ("Read Technical Paper", 20, "#3B82F6"),
        ]

        # Seed sample completion logs for current month up to today
        rng = random.Random(42)
        start_of_month = today.replace(day=1)

        for title, goal, color in habits_catalog:
            habit, _ = Habit.objects.get_or_create(
                user=user,
                title=title,
                defaults={
                    "frequency": "daily",
                    "monthly_goal": goal,
                    "color": color,
                    "is_active": True,
                }
            )

            # Seed logs for active days
            cur = start_of_month
            while cur <= today:
                if rng.random() > 0.40:  # ~60% completion rate for rich charts
                    HabitLog.objects.get_or_create(
                        habit=habit,
                        date=cur,
                        defaults={"status": "completed"}
                    )
                cur += timedelta(days=1)

        self.stdout.write(self.style.SUCCESS("Sample data and executive habit tracker seeded successfully!"))
