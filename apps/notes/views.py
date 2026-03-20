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
