import os
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponseNotFound
from .views import (
    dashboard_view, root_redirect, health_check_view,
    robots_txt_view, sitemap_xml_view, custom_page_not_found_view,
    custom_server_error_view
)
from apps.tasks.calendar_views import calendar_view

# Protected admin URL path (defaults to secure-admin/ to protect against brute-force scans)
ADMIN_URL = os.getenv('DJANGO_ADMIN_URL', 'secure-admin').strip('/')

def admin_decoy_view(request):
    """Decoy view returning 404 for default /admin/ path to prevent automated brute-force attacks."""
    return HttpResponseNotFound("Page not found")

urlpatterns = [
    # Protected Admin Portal (custom path)
    path(f'{ADMIN_URL}/', admin.site.urls),
]

# If admin URL is customized, map decoy to /admin/
if ADMIN_URL != 'admin':
    urlpatterns.append(path('admin/', admin_decoy_view, name='admin_decoy'))

urlpatterns += [
    path('health/', health_check_view, name='health_check'),
    path('robots.txt', robots_txt_view, name='robots_txt'),
    path('sitemap.xml', sitemap_xml_view, name='sitemap_xml'),
    path('', root_redirect, name='root'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('api/', include('apps.api.urls')),
    path('tasks/', include('apps.tasks.urls')),
    path('assignments/', include('apps.assignments.urls')),
    path('habits/', include('apps.habits.urls')),
    path('notes/', include('apps.notes.urls')),
    path('notifications/', include('apps.reminders.urls')),
    path('analytics/', include('apps.analytics.urls')),
    path('calendar/', calendar_view, name='calendar'),
    path('', include('apps.ml_engine.urls')),
    path('', include('apps.accounts.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Custom Error State Handlers (UI/UX Guide State 05 & 103 Things Guide #40)
handler404 = 'config.views.custom_page_not_found_view'
handler500 = 'config.views.custom_server_error_view'
