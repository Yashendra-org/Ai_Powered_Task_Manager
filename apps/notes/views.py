from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import Q
from .models import Note
from .forms import NoteForm


@login_required
def note_list_view(request):
    """
    Quick Notes Scratchpad (Module 7).
    Searchable, card-based with pinned notes always on top.
    """
    user = request.user
    notes = Note.objects.filter(user=user)

    query = request.GET.get('q', '').strip()
    if query:
        notes = notes.filter(Q(title__icontains=query) | Q(content__icontains=query))

    notes = notes.order_by('-is_pinned', '-updated_at')

    context = {
        'notes': notes,
        'search_query': query,
        'total_count': Note.objects.filter(user=user).count(),
    }
    return render(request, 'notes/list.html', context)


@login_required
def note_create_view(request):
    user = request.user
    if request.method == 'POST':
        form = NoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.user = user
            note.save()
            messages.success(request, f"Note '{note.title}' created!")
            return redirect('note_list')
    else:
        form = NoteForm()

    return render(request, 'notes/form.html', {'form': form, 'title': 'Create Note'})


@login_required
def note_edit_view(request, note_id):
    user = request.user
    note = get_object_or_404(Note, id=note_id, user=user)
    if request.method == 'POST':
