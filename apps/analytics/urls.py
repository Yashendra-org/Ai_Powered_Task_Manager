from django.urls import path
from . import views

urlpatterns = [
    path('', views.analytics_dashboard_view, name='analytics_dashboard'),
    path('overview/', views.analytics_dashboard_view, name='analytics_overview'),
    path('dashboard/', views.analytics_dashboard_view, name='analytics_summary'),
]


