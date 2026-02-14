from django.urls import path
from . import views

urlpatterns = [
    path('', views.all_tasks_view, name='all_tasks'),
    path('today/', views.my_day_view, name='my_day'),
    path('create/', views.task_create_view, name='task_create'),
    path('<uuid:task_id>/edit/', views.task_edit_view, name='task_edit'),
    path('<uuid:task_id>/toggle/', views.task_toggle_complete_view, name='task_toggle'),
    path('<uuid:task_id>/delete/', views.task_delete_view, name='task_delete'),
    path('<uuid:task_id>/restore/', views.task_restore_view, name='task_restore'),
    path('<uuid:task_id>/permanent-delete/', views.task_permanent_delete_view, name='task_permanent_delete'),
