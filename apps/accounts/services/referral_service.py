"""
Secure Referral & Anti-Abuse Service.
Implements Google Play & ReelBlink Secure Referral Guidelines:
- Server-side qualification
- Anti-abuse guards: Self-referral prevention, one-time qualification, replay protection
- Atomic server-side claims & duplicate reward prevention
- Immutable reward audit ledger
"""
import uuid
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from apps.accounts.models import ReferralCode, ReferralClaim, RewardHistory, User


def get_or_create_user_referral_code(user: User) -> ReferralCode:
    """Retrieves or generates the unique active referral code for a user."""
    code_obj = ReferralCode.objects.filter(user=user, is_active=True).first()
    if not code_obj:
        unique_code = ReferralCode.generate_unique_code(user)
        code_obj = ReferralCode.objects.create(
            user=user,
            code=unique_code,
            is_active=True
        )
    return code_obj


def process_referral_submission(referrer_code_str: str, referred_user: User, idempotency_key: str = None) -> ReferralClaim:
    """
    Processes a referral redemption request from a newly registered or onboarding user.
    Applies strict anti-abuse rules from the ReelBlink Secure Referral Guide.
    """
    if not idempotency_key:
        idempotency_key = f"claim-{referred_user.id}-{referrer_code_str.strip().upper()}"

    # 1. Idempotency Check (Replay Protection)
    existing_claim = ReferralClaim.objects.filter(idempotency_key=idempotency_key).first()
    if existing_claim:
        return existing_claim

    # 2. Check if this user has already been referred (One-time qualification rule)
    if ReferralClaim.objects.filter(referred_user=referred_user).exists():
        raise ValidationError("This account has already redeemed a referral code and cannot qualify twice.")

    # 3. Find and validate Referral Code
    code_clean = referrer_code_str.strip().upper()
    try:
        referral_code = ReferralCode.objects.select_related('user').get(code=code_clean, is_active=True)
    except ReferralCode.DoesNotExist:
        raise ValidationError("Invalid or inactive referral code.")

    referrer = referral_code.user

    # 4. Anti-Abuse Rule: Self-referral rejection
    if referrer.id == referred_user.id:
        raise ValidationError("Self-referral is strictly forbidden. You cannot use your own referral code.")

    # 5. Anti-Abuse Rule: Existing user posing as new user
    # Check registration age: user must have registered within last 7 days to qualify as new referral
    account_age = timezone.now() - referred_user.date_joined
    if account_age.days > 7:
        # Create rejected claim record for audit trail
        claim = ReferralClaim.objects.create(
            referrer=referrer,
            referred_user=referred_user,
            referral_code=referral_code,
            idempotency_key=idempotency_key,
            status='REJECTED',
            rejection_reason="Account created more than 7 days ago. Only new users qualify for referral rewards.",
            reward_granted=False
        )
        raise ValidationError("Account is outside the new-user referral eligibility window.")

    # 6. Create Initial Pending Claim
    claim = ReferralClaim.objects.create(
        referrer=referrer,
        referred_user=referred_user,
        referral_code=referral_code,
        idempotency_key=idempotency_key,
        status='PENDING'
    )

    # 7. Execute Atomic Qualification & Reward Grant
    qualify_and_reward_claim(claim.id)
    claim.refresh_from_db()
    return claim


@transaction.atomic
def qualify_and_reward_claim(claim_id) -> bool:
    """
    Atomically qualifies a pending referral claim and grants the reward.
    Locks row using select_for_update() to prevent race conditions or double claims.
    """
    claim = ReferralClaim.objects.select_for_update().get(id=claim_id)

    if claim.reward_granted or claim.status in ('REWARDED', 'REJECTED'):
        return False  # Already settled

    now = timezone.now()
    claim.status = 'QUALIFIED'
    claim.qualified_at = now

    # Grant reward to referrer: 7 days Pro Habit Tracking bonus
    RewardHistory.objects.create(
        user=claim.referrer,
        referral_claim=claim,
        reward_type="PRO_DAYS_BONUS",
        units=7
    )

    # Grant welcome bonus to referred user: 7 days Pro Habit Tracking bonus
    RewardHistory.objects.create(
        user=claim.referred_user,
        referral_claim=claim,
        reward_type="WELCOME_BONUS_PRO_DAYS",
        units=7
    )

    claim.reward_granted = True
    claim.status = 'REWARDED'
    claim.rewarded_at = now
    claim.save(update_fields=['status', 'qualified_at', 'reward_granted', 'rewarded_at'])

    return True


def get_user_referral_summary(user: User) -> dict:
    """
    Returns complete referral dashboard statistics and audit history for the user.
    """
    code_obj = get_or_create_user_referral_code(user)
    claims_given = ReferralClaim.objects.filter(referrer=user).select_related('referred_user').order_by('-created_at')
    
    total_invites = claims_given.count()
    rewarded_invites = claims_given.filter(status='REWARDED').count()
    pending_invites = claims_given.filter(status='PENDING').count()

    total_pro_days_earned = sum(
        r.units for r in RewardHistory.objects.filter(user=user)
    )

    referral_received = ReferralClaim.objects.filter(referred_user=user).select_related('referrer').first()

    return {
        'referral_code': code_obj.code,
        'total_invites': total_invites,
        'rewarded_invites': rewarded_invites,
        'pending_invites': pending_invites,
        'total_bonus_days': total_pro_days_earned,
        'claims_list': claims_given[:20],
        'referral_received': referral_received,
        'reward_history': RewardHistory.objects.filter(user=user).order_by('-created_at')[:20],
    }
