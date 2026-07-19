# Stage 2/5: Authentication & deployment refinement
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()


class EmailOrUsernameModelBackend(ModelBackend):
    """
    Custom authentication backend that allows authentication with either
    a username or an email address (case-insensitive).
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
