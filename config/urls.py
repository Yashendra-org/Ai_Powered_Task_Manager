# Stage 3/5: Implementation refinement
import os
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponseNotFound
from .views import dashboard_view, root_redirect
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
    path('', root_redirect, name='root'),
