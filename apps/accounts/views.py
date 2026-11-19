from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserRegisterForm, UserLoginForm, UserProfileForm, DeleteAccountForm


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
