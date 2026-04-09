from django.urls import path
from . import views

urlpatterns = [
    path('', views.assignment_list_view, name='assignment_list'),
    path('create/', views.assignment_create_view, name='assignment_create'),
    path('<uuid:assignment_id>/edit/', views.assignment_edit_view, name='assignment_edit'),
    path('<uuid:assignment_id>/delete/', views.assignment_delete_view, name='assignment_delete'),
    path('<uuid:assignment_id>/submit/', views.assignment_submit_toggle_view, name='assignment_submit_toggle'),
    path('subjects/', views.subject_list_view, name='subject_list'),
    path('subjects/<int:subject_id>/delete/', views.subject_delete_view, name='subject_delete'),
    path('teachers/', views.teacher_list_view, name='teacher_list'),
]

