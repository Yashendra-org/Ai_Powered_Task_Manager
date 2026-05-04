from django.urls import path
from . import views

urlpatterns = [
    path('', views.note_list_view, name='note_list'),
    path('create/', views.note_create_view, name='note_create'),
    path('<int:note_id>/edit/', views.note_edit_view, name='note_edit'),
    path('<int:note_id>/delete/', views.note_delete_view, name='note_delete'),
