# Stage 3/5: Implementation refinement
from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from .views import register_view, CustomLoginView, custom_logout_view, settings_view, profile_view

urlpatterns = [
    # Authentication & Profile
    path('register/', register_view, name='register'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', custom_logout_view, name='logout'),
    path('profile/', profile_view, name='profile'),
    path('settings/', settings_view, name='settings'),

    # Complete Password Reset Flow
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='accounts/password_reset.html',
        email_template_name='accounts/password_reset_email.html',
        subject_template_name='accounts/password_reset_subject.txt',
        success_url=reverse_lazy('password_reset_done')
    ), name='password_reset'),

    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
