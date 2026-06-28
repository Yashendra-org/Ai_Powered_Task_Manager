# Stage 4/5: Progressive implementation
from django import forms
from .models import Habit


class HabitForm(forms.ModelForm):
    scheduled_days = forms.MultipleChoiceField(
        choices=[
            ('0', 'Monday'),
            ('1', 'Tuesday'),
            ('2', 'Wednesday'),
            ('3', 'Thursday'),
            ('4', 'Friday'),
            ('5', 'Saturday'),
            ('6', 'Sunday'),
        ],
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'h-4 w-4 text-emerald-600 focus:ring-emerald-500 border-slate-300 rounded'
        })
    )

    class Meta:
        model = Habit
        fields = ['title', 'description', 'frequency', 'scheduled_days', 'target_time', 'monthly_goal', 'color']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-3.5 py-2.5 text-sm bg-white border border-slate-300 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-colors',
                'placeholder': 'e.g. Daily DSA Practice (1 Hour)'
            }),
            'description': forms.Textarea(attrs={
                'rows': 2,
                'class': 'w-full px-3.5 py-2.5 text-sm bg-white border border-slate-300 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-colors',
                'placeholder': 'Why this habit matters or what milestones you want to hit...'
            }),
            'frequency': forms.Select(attrs={
                'class': 'w-full px-3.5 py-2.5 text-sm bg-white border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-colors'
            }),
            'target_time': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'w-full px-3.5 py-2.5 text-sm bg-white border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-colors'
            }),
            'monthly_goal': forms.NumberInput(attrs={
                'class': 'w-full px-3.5 py-2.5 text-sm bg-white border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-colors',
                'min': '1',
                'max': '365',
                'placeholder': 'e.g. 20'
            }),
            'color': forms.TextInput(attrs={
                'type': 'color',
                'class': 'h-10 w-24 p-1 bg-white border border-slate-300 rounded-lg cursor-pointer focus:outline-none focus:ring-2 focus:ring-emerald-500'
