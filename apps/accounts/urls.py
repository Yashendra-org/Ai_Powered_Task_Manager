from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from .views import (
    register_view, CustomLoginView, custom_logout_view,
    settings_view, profile_view, delete_account_view,
    referral_hub_view, referral_redeem_view
)

urlpatterns = [
    # Primary Authentication Routes
    path('login/', CustomLoginView.as_view(), name='login'),
    path('register/', register_view, name='register'),
    path('logout/', custom_logout_view, name='logout'),

    # Enterprise /auth/ Namespaced Aliases
    path('auth/login/', CustomLoginView.as_view(), name='auth_login'),
    path('auth/register/', register_view, name='auth_register'),
    path('auth/logout/', custom_logout_view, name='auth_logout'),

    # Primary Profile & Settings Routes
    path('profile/', profile_view, name='profile'),
    path('settings/', settings_view, name='settings'),
    path('delete-account/', delete_account_view, name='delete_account'),

    # Enterprise /account/ Namespaced Routes
    path('account/profile/', profile_view, name='account_profile'),
    path('account/settings/', settings_view, name='account_settings'),
    path('account/delete/', delete_account_view, name='account_delete'),
    path('account/referrals/', referral_hub_view, name='account_referrals'),
    path('account/referrals/redeem/', referral_redeem_view, name='account_referrals_redeem'),

    # Secure Referral System (ReelBlink Guide)
    path('referrals/', referral_hub_view, name='referrals'),
    path('referrals/redeem/', referral_redeem_view, name='referrals_redeem'),

    # Complete Password Reset Flow
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='accounts/password_reset.html',
        email_template_name='accounts/password_reset_email.html',
        subject_template_name='accounts/password_reset_subject.txt',
        success_url=reverse_lazy('password_reset_done')
    ), name='password_reset'),
    path('auth/password-reset/', auth_views.PasswordResetView.as_view(
        template_name='accounts/password_reset.html',
        email_template_name='accounts/password_reset_email.html',
        subject_template_name='accounts/password_reset_subject.txt',
        success_url=reverse_lazy('password_reset_done')
    )),

    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='accounts/password_reset_done.html'
    ), name='password_reset_done'),
    path('auth/password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='accounts/password_reset_done.html'
    )),

    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='accounts/password_reset_confirm.html',
        success_url=reverse_lazy('password_reset_complete')
    ), name='password_reset_confirm'),
    path('auth/password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='accounts/password_reset_confirm.html',
        success_url=reverse_lazy('password_reset_complete')
    )),

    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='accounts/password_reset_complete.html'
    ), name='password_reset_complete'),
    path('auth/password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='accounts/password_reset_complete.html'
    )),
]
