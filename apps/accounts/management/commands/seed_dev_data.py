from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.tasks.models import Category, Task
from apps.assignments.models import Subject, Teacher, Assignment
from apps.habits.models import Habit, HabitLog

User = get_user_model()


class Command(BaseCommand):
    help = "Seed initial development user and sample data for My Habbit Tracker"

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
            }
        )
        if created:
            user.set_password("password123")
            user.save()
            self.stdout.write(self.style.SUCCESS("Created dev user: student / password123 (Superuser)"))
        else:
            self.stdout.write("User 'student' already exists.")

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
