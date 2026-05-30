from django.contrib import admin
from .models import Reminder, Notification


@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = ('user', 'reminder_type', 'scheduled_at', 'status', 'sent_at')
    list_filter = ('reminder_type', 'status', 'user')

