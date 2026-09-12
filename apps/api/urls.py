# Stage 3/5: Implementation refinement
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
