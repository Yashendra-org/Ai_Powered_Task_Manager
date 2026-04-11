from django.urls import path
from . import views

urlpatterns = [
    path('', views.habit_list_view, name='habit_list'),
    path('create/', views.habit_create_view, name='habit_create'),
    path('<int:habit_id>/edit/', views.habit_edit_view, name='habit_edit'),
    path('<int:habit_id>/delete/', views.habit_delete_view, name='habit_delete'),
