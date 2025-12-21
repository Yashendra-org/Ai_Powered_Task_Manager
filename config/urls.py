from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .views import dashboard_view, root_redirect
from apps.tasks.calendar_views import calendar_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', root_redirect, name='root'),
