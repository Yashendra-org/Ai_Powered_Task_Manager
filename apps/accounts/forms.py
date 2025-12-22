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
