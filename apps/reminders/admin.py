from django.contrib import admin
from .models import Reminder, Notification


@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
