from django.urls import path
from . import views

urlpatterns = [
    # Primary Workflow Routes
    path('review/', views.end_of_day_review_view, name='end_of_day_review'),
    path('review/apply/', views.apply_rollover_view, name='apply_rollover'),
    path('assistant/', views.smart_assistant_view, name='smart_assistant'),
    path('assistant/recommendations/<int:rec_id>/<str:action>/', views.recommendation_feedback_view, name='recommendation_feedback'),

    # Enterprise /ai/ Scoped Routes
    path('ai/assistant/', views.smart_assistant_view, name='ai_assistant'),
    path('ai/review/', views.end_of_day_review_view, name='ai_review'),
    path('ai/review/apply/', views.apply_rollover_view, name='ai_review_apply'),
    path('ai/recommendations/<int:rec_id>/<str:action>/', views.recommendation_feedback_view, name='ai_recommendation_feedback'),
]

