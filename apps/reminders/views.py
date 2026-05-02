from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.contrib import messages
from .models import Notification


@login_required
def notification_list_view(request):
    """
    In-App Notification Center (Module 6).
    Displays deadline alerts, habit reminders, and system announcements.
    """
    user = request.user
    notifications = Notification.objects.filter(user=user).order_by('-created_at')
    unread_count = notifications.filter(is_read=False).count()

    context = {
