from django import forms
from .models import Assignment, Subject, Teacher


class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name', 'code']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3.5 py-2.5 text-sm bg-white border border-slate-300 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors',
                'placeholder': 'e.g. Database Management Systems'
            }),
            'code': forms.TextInput(attrs={
                'class': 'w-full px-3.5 py-2.5 text-sm bg-white border border-slate-300 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors',
                'placeholder': 'e.g. CS302'
            }),
        }


class TeacherForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = ['name', 'email']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3.5 py-2.5 text-sm bg-white border border-slate-300 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors',
                'placeholder': 'e.g. Dr. R. Sharma'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-3.5 py-2.5 text-sm bg-white border border-slate-300 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors',
                'placeholder': 'sharma@college.edu'
            }),
        }


class AssignmentForm(forms.ModelForm):
    due_at = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={
            'type': 'datetime-local',
            'class': 'w-full px-3.5 py-2.5 text-sm bg-white border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors'
        })
    )

    class Meta:
        model = Assignment
        fields = [
            'title',
            'subject',
            'teacher',
            'description',
            'due_at',
            'priority',
            'status',
            'attachment',
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-3.5 py-2.5 text-sm bg-white border border-slate-300 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors',
                'placeholder': 'e.g. Assignment 3: B+ Trees & Indexing'
            }),
            'subject': forms.Select(attrs={
                'class': 'w-full px-3.5 py-2.5 text-sm bg-white border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors'
            }),
            'teacher': forms.Select(attrs={
                'class': 'w-full px-3.5 py-2.5 text-sm bg-white border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors'
            }),
            'description': forms.Textarea(attrs={
                'rows': 3,
                'class': 'w-full px-3.5 py-2.5 text-sm bg-white border border-slate-300 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors',
                'placeholder': 'Instructions, problem numbers, or submission guidelines...'
            }),
            'priority': forms.Select(attrs={
                'class': 'w-full px-3.5 py-2.5 text-sm bg-white border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors'
            }),
            'status': forms.Select(attrs={
                'class': 'w-full px-3.5 py-2.5 text-sm bg-white border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors'
            }),
            'attachment': forms.FileInput(attrs={
                'class': 'w-full px-3.5 py-2 text-sm bg-white border border-slate-300 rounded-lg text-slate-700 file:mr-4 file:py-1 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100'
            }),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['subject'].queryset = Subject.objects.filter(user=user)
            self.fields['teacher'].queryset = Teacher.objects.filter(user=user)
        self.fields['teacher'].empty_label = "No Instructor Assigned"

