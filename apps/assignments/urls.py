from django.urls import path
from . import views

urlpatterns = [
    path('', views.assignment_list_view, name='assignment_list'),
