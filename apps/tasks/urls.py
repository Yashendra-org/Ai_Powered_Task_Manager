from django.urls import path
from . import views

urlpatterns = [
    path('', views.all_tasks_view, name='all_tasks'),
    path('today/', views.my_day_view, name='my_day'),
