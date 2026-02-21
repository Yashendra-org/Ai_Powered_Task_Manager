from django import forms
from .models import Task, Category


class TaskForm(forms.ModelForm):
    scheduled_start = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={
            'type': 'datetime-local',
            'class': 'w-full px-3.5 py-2.5 text-sm bg-white border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors'
        })
    )
    due_at = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={
            'type': 'datetime-local',
            'class': 'w-full px-3.5 py-2.5 text-sm bg-white border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors'
        })
    )

    class Meta:
        model = Task
        fields = [
            'title',
            'description',
            'category',
            'priority',
            'scheduled_start',
            'due_at',
            'estimated_duration',
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-3.5 py-2.5 text-sm bg-white border border-slate-300 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors',
                'placeholder': 'e.g. Solve 5 Graph problems in DSA'
            }),
            'description': forms.Textarea(attrs={
                'rows': 3,
                'class': 'w-full px-3.5 py-2.5 text-sm bg-white border border-slate-300 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors',
                'placeholder': 'Add details, sub-steps, or references (optional)'
            }),
            'category': forms.Select(attrs={
                'class': 'w-full px-3.5 py-2.5 text-sm bg-white border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors'
            }),
            'priority': forms.Select(attrs={
                'class': 'w-full px-3.5 py-2.5 text-sm bg-white border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors'
            }),
            'estimated_duration': forms.NumberInput(attrs={
                'class': 'w-full px-3.5 py-2.5 text-sm bg-white border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors',
                'placeholder': '30'
            }),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['category'].queryset = Category.objects.filter(user=user)
        self.fields['category'].empty_label = "No Category (General)"


class QuickTaskForm(forms.Form):
    title = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'w-full pl-10 pr-24 py-3 bg-white border border-slate-200 rounded-xl text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 shadow-sm transition-all',
            'placeholder': '+ Add a task to My Day... press Enter'
        })
    )
    priority = forms.ChoiceField(
        choices=Task.PRIORITY_CHOICES,
        initial='medium',
        required=False,
    )
    estimated_duration = forms.IntegerField(
        initial=30,
