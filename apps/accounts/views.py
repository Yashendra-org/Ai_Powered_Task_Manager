import csv
import json
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.utils import timezone
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.urls import reverse
from .forms import UserRegisterForm, UserLoginForm, UserProfileForm, DeleteAccountForm, ReferralRedeemForm
from .models import record_audit_event
from .services.referral_service import get_user_referral_summary, process_referral_submission
from apps.tasks.models import Task, Category
from apps.habits.models import Habit
from apps.notes.models import Note
from apps.assignments.models import Assignment


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='apps.accounts.backends.EmailOrUsernameModelBackend')
            messages.success(request, f"Welcome to My Habbit Tracker, {user.username}!")
            return redirect('dashboard')
    else:
        form = UserRegisterForm()
    
    return render(request, 'accounts/register.html', {'form': form})


class CustomLoginView(LoginView):
    form_class = UserLoginForm
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

    def form_valid(self, form):
        user = form.get_user()
        record_audit_event(user, 'LOGIN', self.request, f"User {user.username} signed in successfully")
        messages.success(self.request, f"Welcome back, {user.username}!")
        return super().form_valid(form)


def custom_logout_view(request):
    if request.user.is_authenticated:
        record_audit_event(request.user, 'LOGOUT', request, f"User {request.user.username} signed out")
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('login')


@login_required
def profile_view(request):
    user = request.user
    stats = {
        'tasks_completed': Task.objects.filter(user=user, status='completed').count(),
        'tasks_pending': Task.objects.filter(user=user, status='pending').count(),
        'habits_active': Habit.objects.filter(user=user, is_active=True).count(),
        'assignments_submitted': Assignment.objects.filter(user=user, status='submitted').count(),
    }
    return render(request, 'accounts/profile.html', {'user': user, 'stats': stats})


@login_required
def settings_view(request):
    delete_form = DeleteAccountForm(user=request.user)
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            record_audit_event(request.user, 'SETTINGS_UPDATE', request, "Updated account & accessibility preferences")
            messages.success(request, "Your preferences have been updated.")
            return redirect('settings')
    else:
        form = UserProfileForm(instance=request.user)
    
    audit_logs = request.user.audit_logs.all()[:20]
    return render(request, 'accounts/settings.html', {
        'form': form,
        'delete_form': delete_form,
        'audit_logs': audit_logs,
    })


@login_required
def export_data_json_view(request):
    """
    Pillar 2, #8: Self-Service Zero-Knowledge Data Portability & GDPR Exporter (JSON).
    Generates a full structured archive of the user's workspace.
    """
    user = request.user
    tasks = Task.objects.filter(user=user).select_related('category')
    habits = Habit.objects.filter(user=user)
    notes = Note.objects.filter(user=user)
    assignments = Assignment.objects.filter(user=user)

    export_payload = {
        "metadata": {
            "app": "My Habit Tracker",
            "version": "1.0.0",
            "exported_at": timezone.now().isoformat(),
            "user": {
                "username": user.username,
                "email": user.email,
                "timezone": user.timezone,
                "date_joined": user.date_joined.isoformat() if user.date_joined else None,
            }
        },
        "tasks": [
            {
                "id": str(t.id),
                "title": t.title,
                "description": t.description,
                "category": t.category.name if t.category else None,
                "priority": t.priority,
                "status": t.status,
                "estimated_duration": t.estimated_duration,
                "due_at": t.due_at.isoformat() if t.due_at else None,
                "completed_at": t.completed_at.isoformat() if t.completed_at else None,
                "created_at": t.created_at.isoformat(),
            }
            for t in tasks
        ],
        "habits": [
            {
                "id": h.id,
                "title": h.title,
                "frequency": h.frequency,
                "monthly_goal": h.monthly_goal,
                "color": h.color,
                "is_active": h.is_active,
                "created_at": h.created_at.isoformat(),
            }
            for h in habits
        ],
        "notes": [
            {
                "id": str(n.id),
                "title": n.title,
                "content": n.content,
                "is_pinned": n.is_pinned,
                "created_at": n.created_at.isoformat(),
            }
            for n in notes
        ],
        "assignments": [
            {
                "id": str(a.id),
                "title": a.title,
                "subject": a.subject,
                "due_date": a.due_date.isoformat() if a.due_date else None,
                "status": a.status,
                "grade": a.grade,
                "created_at": a.created_at.isoformat(),
            }
            for a in assignments
        ]
    }

    record_audit_event(user, 'EXPORT_JSON', request, "Exported full account backup in JSON format")
    response = HttpResponse(json.dumps(export_payload, indent=2), content_type='application/json')
    filename = f"habittracker_backup_{user.username}_{timezone.localdate().strftime('%Y%m%d')}.json"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required
def export_data_csv_view(request):
    """
    Pillar 2, #8: Tabular Task Exporter (CSV).
    Generates an RFC 4180 CSV spreadsheet of all tasks.
    """
    user = request.user
    tasks = Task.objects.filter(user=user).select_related('category').order_by('-created_at')

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    filename = f"habittracker_tasks_{user.username}_{timezone.localdate().strftime('%Y%m%d')}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow([
        'ID', 'Title', 'Description', 'Category', 'Priority',
        'Status', 'Estimated Duration (Mins)', 'Due At', 'Completed At', 'Created At'
    ])

    for t in tasks:
        writer.writerow([
            str(t.id),
            t.title,
            t.description,
            t.category.name if t.category else '',
            t.priority,
            t.status,
            t.estimated_duration,
            t.due_at.isoformat() if t.due_at else '',
            t.completed_at.isoformat() if t.completed_at else '',
            t.created_at.isoformat(),
        ])

    record_audit_event(user, 'EXPORT_CSV', request, "Exported tasks backlog in CSV format")
    return response


@login_required
def export_data_ics_view(request):
    """
    Pillar 4, #15 & Pillar 2, #8: RFC 5545 iCalendar Exporter.
    Generates standards-compliant .ics schedule importable into Google Calendar, Apple Calendar, and Outlook.
    """
    user = request.user
    tasks = Task.objects.filter(user=user, due_at__isnull=False).order_by('due_at')

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//My Habit Tracker//Task & Schedule Exporter 1.0//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:HabitTracker - {user.username}",
        "X-WR-TIMEZONE:" + (user.timezone or "Asia/Kolkata"),
    ]

    now_str = timezone.now().strftime("%Y%m%dT%H%M%SZ")

    for t in tasks:
        start_time = t.due_at
        end_time = start_time + timezone.timedelta(minutes=max(15, t.estimated_duration))
        dtstart = start_time.strftime("%Y%m%dT%H%M%SZ")
        dtend = end_time.strftime("%Y%m%dT%H%M%SZ")

        clean_summary = t.title.replace("\n", " ").replace(";", "\\;").replace(",", "\\,")
        clean_desc = (t.description or "").replace("\n", "\\n").replace(";", "\\;").replace(",", "\\,")

        priority_val = "1" if t.priority == 'high' else ("5" if t.priority == 'medium' else "9")
        status_val = "COMPLETED" if t.status == 'completed' else "CONFIRMED"

        lines.append("BEGIN:VEVENT")
        lines.append(f"UID:{t.id}@habittracker.app")
        lines.append(f"DTSTAMP:{now_str}")
        lines.append(f"DTSTART:{dtstart}")
        lines.append(f"DTEND:{dtend}")
        lines.append(f"SUMMARY:{clean_summary}")
        if clean_desc:
            lines.append(f"DESCRIPTION:{clean_desc}")
        lines.append(f"STATUS:{status_val}")
        lines.append(f"PRIORITY:{priority_val}")
        lines.append("END:VEVENT")

    lines.append("END:VCALENDAR")

    record_audit_event(user, 'EXPORT_ICS', request, "Exported schedule in RFC 5545 iCalendar format")

    ics_content = "\r\n".join(lines) + "\r\n"
    response = HttpResponse(ics_content, content_type='text/calendar; charset=utf-8')
    filename = f"habittracker_schedule_{user.username}_{timezone.localdate().strftime('%Y%m%d')}.ics"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response



@login_required
def delete_account_view(request):
    """
    103 Things Guide (#84) & UI/UX Guide (States 10 & 17):
    Permanently deletes user account, cascade-deletes related records, and invalidates session.
    """
    if request.method != 'POST':
        return redirect('settings')

    form = DeleteAccountForm(request.user, request.POST)
    if not form.is_valid():
        for error in form.errors.get('password', []):
            messages.error(request, error)
        return redirect('settings')

    user = request.user
    logout(request)
    user.delete()
    messages.success(request, "Your account and all associated data have been permanently deleted.")
    return redirect('login')


@login_required
def referral_hub_view(request):
    """
    Renders the Referral & Friend Invitation Hub.
    Displays user referral code, share link, invite stats, and reward history.
    """
    summary = get_user_referral_summary(request.user)
    redeem_form = ReferralRedeemForm()
    share_url = request.build_absolute_uri(reverse('register')) + f"?ref={summary['referral_code']}"

    context = {
        'summary': summary,
        'redeem_form': redeem_form,
        'share_url': share_url,
    }
    return render(request, 'accounts/referrals.html', context)


@login_required
def referral_redeem_view(request):
    """
    Handles submission of a referral code by an authenticated user.
    """
    if request.method != 'POST':
        return redirect('referrals')

    form = ReferralRedeemForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Please enter a valid referral code.")
        return redirect('referrals')

    code_str = form.cleaned_data['code']
    try:
        process_referral_submission(code_str, request.user)
        messages.success(request, f"Referral code '{code_str}' redeemed successfully! You both earned 7 Pro bonus days!")
    except ValidationError as e:
        messages.error(request, str(e.message if hasattr(e, 'message') else e))

    return redirect('referrals')

