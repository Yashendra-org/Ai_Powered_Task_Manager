from django.urls import path
from . import views

urlpatterns = [
    path('', views.habit_list_view, name='habit_list'),
    path('create/', views.habit_create_view, name='habit_create'),
