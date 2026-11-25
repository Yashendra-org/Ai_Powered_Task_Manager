from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.urls import reverse
from .forms import UserRegisterForm, UserLoginForm, UserProfileForm, DeleteAccountForm, ReferralRedeemForm
from .services.referral_service import get_user_referral_summary, process_referral_submission


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='apps.accounts.backends.EmailOrUsernameModelBackend')
            messages.success(request, f"Welcome to My Habbit Tracker, {user.username}!")
            return redirect('dashboard')
    else:
        form = UserRegisterForm()
    
    return render(request, 'accounts/register.html', {'form': form})


class CustomLoginView(LoginView):
    form_class = UserLoginForm
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

    def form_valid(self, form):
        messages.success(self.request, f"Welcome back, {form.get_user().username}!")
        return super().form_valid(form)


def custom_logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('login')


@login_required
def profile_view(request):
    user = request.user
    from apps.tasks.models import Task
    from apps.habits.models import Habit
    from apps.assignments.models import Assignment

    stats = {
        'tasks_completed': Task.objects.filter(user=user, status='completed').count(),
        'tasks_pending': Task.objects.filter(user=user, status='pending').count(),
        'habits_active': Habit.objects.filter(user=user, is_active=True).count(),
        'assignments_submitted': Assignment.objects.filter(user=user, status='submitted').count(),
    }
    return render(request, 'accounts/profile.html', {'user': user, 'stats': stats})


@login_required
def settings_view(request):
    delete_form = DeleteAccountForm(user=request.user)
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your preferences have been updated.")
            return redirect('settings')
    else:
        form = UserProfileForm(instance=request.user)
    
    return render(request, 'accounts/settings.html', {'form': form, 'delete_form': delete_form})


@login_required
def delete_account_view(request):
    """
    103 Things Guide (#84) & UI/UX Guide (States 10 & 17):
    Permanently deletes user account, cascade-deletes related records, and invalidates session.
    """
    if request.method != 'POST':
        return redirect('settings')

    form = DeleteAccountForm(request.user, request.POST)
    if not form.is_valid():
        for error in form.errors.get('password', []):
            messages.error(request, error)
        return redirect('settings')

    user = request.user
    logout(request)
    user.delete()
    messages.success(request, "Your account and all associated data have been permanently deleted.")
    return redirect('login')


@login_required
def referral_hub_view(request):
    """
    Renders the Referral & Friend Invitation Hub.
    Displays user referral code, share link, invite stats, and reward history.
    """
    summary = get_user_referral_summary(request.user)
    redeem_form = ReferralRedeemForm()
    share_url = request.build_absolute_uri(reverse('register')) + f"?ref={summary['referral_code']}"

    context = {
        'summary': summary,
        'redeem_form': redeem_form,
        'share_url': share_url,
    }
    return render(request, 'accounts/referrals.html', context)


@login_required
def referral_redeem_view(request):
    """
    Handles submission of a referral code by an authenticated user.
    """
    if request.method != 'POST':
        return redirect('referrals')

    form = ReferralRedeemForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Please enter a valid referral code.")
        return redirect('referrals')

    code_str = form.cleaned_data['code']
    try:
        process_referral_submission(code_str, request.user)
        messages.success(request, f"Referral code '{code_str}' redeemed successfully! You both earned 7 Pro bonus days!")
    except ValidationError as e:
        messages.error(request, str(e.message if hasattr(e, 'message') else e))

    return redirect('referrals')

