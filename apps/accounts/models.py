import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model with UUID primary key, timezone preferences,
    and configurable end-of-day daily review timing.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, verbose_name="Email Address")
    timezone = models.CharField(max_length=64, default="Asia/Kolkata", help_text="User's preferred timezone")
    daily_review_time = models.TimeField(default="21:30", help_text="Time to trigger the daily summary & review")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "accounts_user"
        ordering = ["-date_joined"]

    def __str__(self):
        return self.username
