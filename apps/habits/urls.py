# Stage 3/5: Progressive implementation
from django.urls import path
from . import views

urlpatterns = [
    path('', views.habit_list_view, name='habit_list'),
    path('export/', views.habit_export_csv_view, name='habit_export_csv'),
    path('create/', views.habit_create_view, name='habit_create'),
