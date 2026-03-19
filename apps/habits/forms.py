from django import forms
from .models import Habit


class HabitForm(forms.ModelForm):
    scheduled_days = forms.MultipleChoiceField(
        choices=[
            ('0', 'Monday'),
            ('1', 'Tuesday'),
