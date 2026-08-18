# Stage 1/5: Implementation refinement
from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from .views import register_view, CustomLoginView, custom_logout_view, settings_view, profile_view

urlpatterns = [
    # Authentication & Profile
    path('register/', register_view, name='register'),
    path('login/', CustomLoginView.as_view(), name='login'),
