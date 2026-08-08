# Stage 1/5: Implementation refinement
import os
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponseNotFound
from .views import dashboard_view, root_redirect
from apps.tasks.calendar_views import calendar_view

# Protected admin URL path (defaults to secure-admin/ to protect against brute-force scans)
