from django.contrib import admin
from .models import MLRecommendation


@admin.register(MLRecommendation)
class MLRecommendationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'recommendation_type', 'confidence_score', 'status', 'created_at')
    list_filter = ('recommendation_type', 'status', 'user')
    search_fields = ('title', 'explanation')
