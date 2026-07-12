from django.urls import path
from . import views

urlpatterns = [
    path('review/', views.end_of_day_review_view, name='end_of_day_review'),
    path('review/apply/', views.apply_rollover_view, name='apply_rollover'),
