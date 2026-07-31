# Stage 2/5: Progressive implementation
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
