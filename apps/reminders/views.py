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
        'notifications': notifications,
        'unread_count': unread_count,
    }
    return render(request, 'reminders/list.html', context)


@login_required
@require_POST
def notification_mark_read_view(request, notification_id):
    user = request.user
    notification = get_object_or_404(Notification, id=notification_id, user=user)
    notification.is_read = True
    notification.save(update_fields=['is_read'])
    unread_count = Notification.objects.filter(user=user, is_read=False).count()
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', '')
    if is_ajax:
        return JsonResponse({'success': True, 'notification_id': str(notification_id), 'unread_count': unread_count})
    return redirect(request.META.get('HTTP_REFERER', 'notification_list'))


@login_required
@require_POST
def notification_mark_all_read_view(request):
    user = request.user
    Notification.objects.filter(user=user, is_read=False).update(is_read=True)
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', '')
    if is_ajax:
        return JsonResponse({'success': True, 'unread_count': 0, 'message': 'All notifications marked as read.'})
    messages.success(request, "All notifications marked as read.")
    return redirect('notification_list')
