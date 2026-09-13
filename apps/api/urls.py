from django.urls import path
from . import views

urlpatterns = [
    # Discovery Root
    path('', views.ApiRootView.as_view(), name='api_root'),
    path('v1/', views.ApiRootView.as_view(), name='api_v1_root'),

    # Tasks API
    path('v1/tasks/', views.TaskListCreateApiView.as_view(), name='api_tasks_list_create'),
    path('v1/tasks/<uuid:pk>/toggle/', views.TaskToggleApiView.as_view(), name='api_tasks_toggle'),

    # Habits API
    path('v1/habits/', views.HabitListApiView.as_view(), name='api_habits_list'),

    # Assignments API
    path('v1/assignments/', views.AssignmentListApiView.as_view(), name='api_assignments_list'),

    # Analytics API
    path('v1/analytics/', views.AnalyticsSummaryApiView.as_view(), name='api_analytics_summary'),
]
