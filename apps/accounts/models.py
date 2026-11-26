import secrets
import string
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
    morning_briefing_time = models.TimeField(default="08:00", help_text="Time to trigger morning planning & task briefing")
    email_notifications = models.BooleanField(default=True, help_text="Receive productivity digests and deadline reminders via email")
    sound_effects = models.BooleanField(default=True, help_text="Play audio cues on task completion and habit check-in")
    week_start_day = models.CharField(
        max_length=10,
        default="monday",
        choices=[('monday', 'Monday'), ('sunday', 'Sunday')],
        help_text="Calendar and habit matrix first day of the week"
    )
    # Power-User & Accessibility Preferences
    keyboard_shortcuts = models.BooleanField(
        default=True,
        help_text="Enable global keyboard shortcuts and quick navigation hotkeys"
    )
    high_contrast = models.BooleanField(
        default=False,
        help_text="Enable high contrast UI mode for enhanced visual readability"
    )
    reduced_motion = models.BooleanField(
        default=False,
        help_text="Minimize UI transitions, layout shifts, and heavy animations"
    )
    default_landing_view = models.CharField(
        max_length=32,
        default="dashboard",
        choices=[
            ('dashboard', 'Executive Dashboard'),
            ('my_day', 'My Day Focus Cockpit'),
            ('all_tasks', 'All Tasks Backlog'),
            ('analytics', 'Productivity Analytics')
        ],
        help_text="Default page destination opened immediately upon sign-in"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "accounts_user"
        ordering = ["-date_joined"]

    def __str__(self):
        return self.username


class ReferralCode(models.Model):
    """
    Referral code assigned to a user for inviting peers.
    Satisfies Google Play / ReelBlink Secure Referral Guidelines.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='referral_codes')
    code = models.CharField(max_length=32, unique=True, db_index=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "accounts_referral_code"
        ordering = ["-created_at"]

    @classmethod
    def generate_unique_code(cls, user):
        prefix = re_sub_alphanumeric(user.username[:4].upper())
        if len(prefix) < 2:
            prefix = "HABIT"
        chars = string.ascii_uppercase + string.digits
        for _ in range(10):
            suffix = ''.join(secrets.choice(chars) for _ in range(6))
            code = f"{prefix}-{suffix}"
            if not cls.objects.filter(code=code).exists():
                return code
        return f"REF-{uuid.uuid4().hex[:8].upper()}"

    def __str__(self):
        return f"{self.user.username} ({self.code})"


def re_sub_alphanumeric(val):
    return "".join(c for c in val if c.isalnum())


class ReferralClaim(models.Model):
    """
    Audit ledger tracking attribution, server-side validation state, and rewards.
    Enforces one-time qualification and replay idempotency.
    """
    STATUS_CHOICES = (
        ('PENDING', 'Pending Validation'),
        ('QUALIFIED', 'Qualified'),
        ('REWARDED', 'Reward Granted'),
        ('REJECTED', 'Rejected / Abuse Detected'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    referrer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='referrals_given')
    referred_user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='referral_received')
    referral_code = models.ForeignKey(ReferralCode, on_delete=models.SET_NULL, null=True, blank=True, related_name='claims')
    idempotency_key = models.CharField(max_length=64, unique=True, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    rejection_reason = models.CharField(max_length=255, blank=True, default="")
    reward_granted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    qualified_at = models.DateTimeField(null=True, blank=True)
    rewarded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "accounts_referral_claim"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.referrer.username} -> {self.referred_user.username} [{self.status}]"


class RewardHistory(models.Model):
    """
    Immutable audit ledger of earned rewards (not just a counter).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reward_history')
    referral_claim = models.ForeignKey(ReferralClaim, on_delete=models.CASCADE, related_name='rewards')
    reward_type = models.CharField(max_length=64, default="PRO_DAYS_BONUS")
    units = models.IntegerField(default=7, help_text="Number of bonus reward units")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "accounts_reward_history"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} earned {self.units} {self.reward_type}"

