from django import forms
from .models import Note


class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ['title', 'content', 'is_pinned']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-3.5 py-2.5 text-sm bg-white border border-slate-300 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-amber-500 transition-colors',
                'placeholder': 'Note title or topic...'
            }),
            'content': forms.Textarea(attrs={
                'rows': 6,
                'class': 'w-full px-3.5 py-2.5 text-sm bg-white border border-slate-300 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-amber-500 transition-colors',
                'placeholder': 'Jot down ideas, study summaries, or meeting reminders...'
            }),
            'is_pinned': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-amber-600 focus:ring-amber-500 border-slate-300 rounded'
            }),
        }

    def clean_title(self):
        title = self.cleaned_data.get('title', '').strip()
        if len(title) > 255:
            raise forms.ValidationError("Note title cannot exceed 255 characters.")
        return title

    def clean_content(self):
        content = self.cleaned_data.get('content', '')
        if len(content) > 50000:
            raise forms.ValidationError("Note content cannot exceed 50,000 characters.")
        return content


