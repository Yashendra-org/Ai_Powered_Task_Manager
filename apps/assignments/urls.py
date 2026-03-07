from django.urls import path
from . import views

urlpatterns = [
    path('', views.assignment_list_view, name='assignment_list'),
    path('create/', views.assignment_create_view, name='assignment_create'),
    path('<uuid:assignment_id>/edit/', views.assignment_edit_view, name='assignment_edit'),
    path('<uuid:assignment_id>/delete/', views.assignment_delete_view, name='assignment_delete'),
