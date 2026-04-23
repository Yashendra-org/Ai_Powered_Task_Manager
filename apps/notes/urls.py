from django.urls import path
from . import views

urlpatterns = [
    path('', views.note_list_view, name='note_list'),
    path('create/', views.note_create_view, name='note_create'),
