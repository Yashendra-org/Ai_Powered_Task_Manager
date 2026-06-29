# Stage 2/5: Progressive implementation
from django.urls import path
from . import views

urlpatterns = [
    path('', views.habit_list_view, name='habit_list'),
