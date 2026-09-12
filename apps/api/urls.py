# Stage 2/5: Implementation refinement
from django.urls import path
from . import views

urlpatterns = [
    # Discovery Root
    path('', views.ApiRootView.as_view(), name='api_root'),
    path('v1/', views.ApiRootView.as_view(), name='api_v1_root'),

    # Tasks API
