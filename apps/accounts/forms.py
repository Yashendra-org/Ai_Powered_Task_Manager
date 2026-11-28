from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none text-slate-800 placeholder-slate-400',
            'placeholder': 'student@college.edu'
        })
    )
    timezone = forms.ChoiceField(
        choices=[
            ('Asia/Kolkata', 'Asia/Kolkata (IST)'),
            ('UTC', 'UTC'),
            ('America/New_York', 'America/New_York (EST)'),
            ('Europe/London', 'Europe/London (GMT)'),
        ],
        initial='Asia/Kolkata',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none text-slate-800 bg-white'
        })
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'timezone')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none text-slate-800 placeholder-slate-400',
                'placeholder': 'username'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for fieldname in ['password1', 'password2']:
            if fieldname in self.fields:
                self.fields[fieldname].widget.attrs.update({
                    'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none text-slate-800 placeholder-slate-400',
                    'placeholder': '••••••••'
                })


class UserLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none text-slate-800 placeholder-slate-400',
            'placeholder': 'username or email'
        })
        self.fields['password'].widget.attrs.update({
            'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none text-slate-800 placeholder-slate-400',
            'placeholder': '••••••••'
        })


class UserProfileForm(forms.ModelForm):
    TIMEZONE_CHOICES = [
        ('Asia/Kolkata', 'Asia/Kolkata (IST - UTC+05:30)'),
        ('UTC', 'UTC (Coordinated Universal Time)'),
        ('America/New_York', 'America/New_York (EST - UTC-05:00)'),
        ('America/Los_Angeles', 'America/Los_Angeles (PST - UTC-08:00)'),
        ('Europe/London', 'Europe/London (GMT/BST - UTC+00:00)'),
        ('Europe/Berlin', 'Europe/Berlin (CET - UTC+01:00)'),
        ('Asia/Tokyo', 'Asia/Tokyo (JST - UTC+09:00)'),
        ('Asia/Singapore', 'Asia/Singapore (SGT - UTC+08:00)'),
        ('Australia/Sydney', 'Australia/Sydney (AEST - UTC+10:00)'),
    ]

    timezone = forms.ChoiceField(
        choices=TIMEZONE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none text-slate-800 bg-white text-sm'
        })
    )
    morning_briefing_time = forms.TimeField(
        required=False,
        widget=forms.TimeInput(attrs={
            'type': 'time',
            'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none text-slate-800 text-sm'
        })
    )
    week_start_day = forms.ChoiceField(
        choices=[('monday', 'Monday'), ('sunday', 'Sunday')],
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none text-slate-800 bg-white text-sm'
        })
    )
    default_landing_view = forms.ChoiceField(
        choices=[
            ('dashboard', 'Executive Dashboard'),
            ('my_day', 'My Day Focus Cockpit'),
            ('all_tasks', 'All Tasks Backlog'),
            ('analytics', 'Productivity Analytics')
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none text-slate-800 bg-white text-sm'
        })
    )
    current_password = forms.CharField(
        required=False,
        label="Current Password (Required to Change Email)",
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none text-slate-800 text-sm placeholder-slate-400',
            'placeholder': 'Enter current password only if changing email',
            'autocomplete': 'current-password'
        })
    )

    class Meta:
        model = User
        fields = (
            'first_name', 'last_name', 'email', 'timezone',
            'morning_briefing_time', 'daily_review_time',
            'email_notifications', 'sound_effects', 'week_start_day',
            'keyboard_shortcuts', 'high_contrast', 'reduced_motion', 'default_landing_view'
        )
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none text-slate-800 text-sm placeholder-slate-400',
                'placeholder': 'First Name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none text-slate-800 text-sm placeholder-slate-400',
                'placeholder': 'Last Name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none text-slate-800 text-sm'
            }),
            'daily_review_time': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none text-slate-800 text-sm'
            }),
            'email_notifications': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue-600 bg-white border-slate-300 rounded focus:ring-blue-500 focus:ring-2 cursor-pointer'
            }),
            'sound_effects': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue-600 bg-white border-slate-300 rounded focus:ring-blue-500 focus:ring-2 cursor-pointer'
            }),
            'keyboard_shortcuts': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue-600 bg-white border-slate-300 rounded focus:ring-blue-500 focus:ring-2 cursor-pointer'
            }),
            'high_contrast': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue-600 bg-white border-slate-300 rounded focus:ring-blue-500 focus:ring-2 cursor-pointer'
            }),
            'reduced_motion': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue-600 bg-white border-slate-300 rounded focus:ring-blue-500 focus:ring-2 cursor-pointer'
            }),
        }

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip().lower()
        if not email:
            raise forms.ValidationError("A valid email address is required.")
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("This email address is already associated with another account.")
        return email

    def clean_morning_briefing_time(self):
        val = self.cleaned_data.get('morning_briefing_time')
        return val or getattr(self.instance, 'morning_briefing_time', None) or '08:00'

    def clean_week_start_day(self):
        val = self.cleaned_data.get('week_start_day')
        return val or getattr(self.instance, 'week_start_day', None) or 'monday'

    def clean_default_landing_view(self):
        val = self.cleaned_data.get('default_landing_view')
        return val or getattr(self.instance, 'default_landing_view', None) or 'dashboard'

    def clean(self):
        cleaned_data = super().clean()
        new_email = (cleaned_data.get('email') or '').strip().lower()
        original_email = (getattr(self.instance, 'email', '') or '').strip().lower()
        if new_email and original_email and new_email != original_email:
            current_pw = cleaned_data.get('current_password') or ''
            if not self.instance.check_password(current_pw):
                self.add_error(
                    'current_password',
                    "Please enter your current password to authorize changing your email address."
                )
        return cleaned_data




class DeleteAccountForm(forms.Form):
    """
    103 Things Guide (#84) & UI/UX Guide (States 10 & 17):
    Secure confirmation form requiring password re-authentication before account deletion.
    """
    password = forms.CharField(
        label="Current Password",
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500 outline-none text-slate-800 placeholder-slate-400',
            'placeholder': 'Enter your password to confirm'
        })
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if not self.user.check_password(password):
            raise forms.ValidationError("Incorrect password. Please enter your correct password to confirm deletion.")
        return password


class ReferralRedeemForm(forms.Form):
    """
    Form to redeem a peer invitation / referral code.
    """
    code = forms.CharField(
        label="Referral / Invite Code",
        max_length=32,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none text-slate-800 placeholder-slate-400 uppercase tracking-widest',
            'placeholder': 'CODE-123456',
            'autocomplete': 'off',
            'spellcheck': 'false'
        })
    )

    def clean_code(self):
        code = self.cleaned_data.get('code', '').strip().upper()
        if not code:
            raise forms.ValidationError("Please enter a valid referral code.")
        return code


