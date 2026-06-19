from django.urls import path
from . import views

urlpatterns = [
    path('review/', views.end_of_day_review_view, name='end_of_day_review'),
    path('review/apply/', views.apply_rollover_view, name='apply_rollover'),
    path('assistant/', views.smart_assistant_view, name='smart_assistant'),
    path('assistant/recommendations/<int:rec_id>/<str:action>/', views.recommendation_feedback_view, name='recommendation_feedback'),
]

