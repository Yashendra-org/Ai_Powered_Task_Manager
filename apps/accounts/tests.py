from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.tasks.models import Task

User = get_user_model()


class AuthenticationAndDashboardTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('register')
        self.login_url = reverse('login')
        self.dashboard_url = reverse('dashboard')
        self.settings_url = reverse('settings')
        self.delete_account_url = reverse('delete_account')

    def test_registration_view_renders(self):
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/register.html')

    def test_login_view_renders(self):
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/login.html')

    def test_user_registration_and_login_flow(self):
        post_data = {
            'username': 'student_yashendra',
            'email': 'student@example.com',
            'timezone': 'Asia/Kolkata',
            'password1': 'StrongP@ssw0rd123!',
            'password2': 'StrongP@ssw0rd123!',
        }
        response = self.client.post(self.register_url, post_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['user'].is_authenticated)
        self.assertEqual(response.context['user'].username, 'student_yashendra')
        self.assertEqual(response.context['user'].timezone, 'Asia/Kolkata')
        self.assertTemplateUsed(response, 'dashboard/index.html')

    def test_dashboard_requires_authentication(self):
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/login/'))

    def test_settings_view_updates_preferences(self):
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPassword123!',
            timezone='Asia/Kolkata',
            daily_review_time='21:30'
        )
        self.client.login(username='testuser', password='TestPassword123!')
        
        response = self.client.get(self.settings_url)
        self.assertEqual(response.status_code, 200)

        # Update settings
        update_data = {
            'first_name': 'Alex',
            'last_name': 'Dev',
            'email': 'updated@example.com',
            'timezone': 'UTC',
            'morning_briefing_time': '07:30:00',
            'daily_review_time': '22:00:00',
            'week_start_day': 'sunday',
            'email_notifications': 'on',
            'sound_effects': 'on',
        }
        post_response = self.client.post(self.settings_url, update_data, follow=True)
        self.assertEqual(post_response.status_code, 200)
        
        user.refresh_from_db()
        self.assertEqual(user.first_name, 'Alex')
        self.assertEqual(user.last_name, 'Dev')
        self.assertEqual(user.email, 'updated@example.com')
        self.assertEqual(user.timezone, 'UTC')
        self.assertEqual(str(user.morning_briefing_time), '07:30:00')
        self.assertEqual(str(user.daily_review_time), '22:00:00')
        self.assertEqual(user.week_start_day, 'sunday')
        self.assertTrue(user.email_notifications)
        self.assertTrue(user.sound_effects)


    def test_account_deletion_requires_authentication(self):
        response = self.client.post(self.delete_account_url, {'password': 'any'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/login/'))

    def test_account_deletion_rejects_incorrect_password(self):
        user = User.objects.create_user(
            username='deluser_fail',
            email='delfail@example.com',
            password='CorrectPassword123!'
        )
        self.client.login(username='deluser_fail', password='CorrectPassword123!')
        
        response = self.client.post(self.delete_account_url, {'password': 'WrongPassword999!'}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(username='deluser_fail').exists())

    def test_account_deletion_with_correct_password(self):
        user = User.objects.create_user(
            username='deluser_success',
            email='delsuccess@example.com',
            password='CorrectPassword123!'
        )
        self.client.login(username='deluser_success', password='CorrectPassword123!')
        
        response = self.client.post(self.delete_account_url, {'password': 'CorrectPassword123!'}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='deluser_success').exists())

    def test_account_deletion_cascades_to_user_tasks(self):
        user = User.objects.create_user(
            username='deluser_cascade',
            email='delcascade@example.com',
            password='Password123!'
        )
        Task.objects.create(user=user, title='Task to be cascade deleted')
        self.assertEqual(Task.objects.filter(user=user).count(), 1)

        self.client.login(username='deluser_cascade', password='Password123!')
        response = self.client.post(self.delete_account_url, {'password': 'Password123!'}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='deluser_cascade').exists())
        self.assertEqual(Task.objects.filter(user=user).count(), 0)


class SecureReferralSystemTests(TestCase):
    """
    Automated verification of Google Play & ReelBlink Secure Referral Anti-Abuse Rules:
    1. Genuine referral succeeds and creates atomic reward history
    2. Self-referral fails
    3. Same account cannot qualify twice (one-time qualification)
    4. Existing user beyond eligibility window cannot qualify
    5. Replayed request creates no second reward (idempotency)
    6. Referral dashboard and redemption views require auth and function correctly
    """

    def setUp(self):
        from apps.accounts.services.referral_service import get_or_create_user_referral_code
        self.referrer = User.objects.create_user(
            username='referrer_user',
            email='referrer@example.com',
            password='TestPassword123!'
        )
        self.ref_code_obj = get_or_create_user_referral_code(self.referrer)
        self.referred = User.objects.create_user(
            username='referred_user',
            email='referred@example.com',
            password='TestPassword123!'
        )

    def test_genuine_referral_succeeds_and_rewards_both(self):
        from apps.accounts.services.referral_service import process_referral_submission
        from apps.accounts.models import RewardHistory
        claim = process_referral_submission(self.ref_code_obj.code, self.referred)
        self.assertEqual(claim.status, 'REWARDED')
        self.assertTrue(claim.reward_granted)
        self.assertEqual(claim.referrer, self.referrer)
        self.assertEqual(claim.referred_user, self.referred)

        # Check reward ledger
        referrer_rewards = RewardHistory.objects.filter(user=self.referrer)
        referred_rewards = RewardHistory.objects.filter(user=self.referred)
        self.assertEqual(referrer_rewards.count(), 1)
        self.assertEqual(referrer_rewards.first().units, 7)
        self.assertEqual(referred_rewards.count(), 1)
        self.assertEqual(referred_rewards.first().units, 7)

    def test_self_referral_fails(self):
        from django.core.exceptions import ValidationError
        from apps.accounts.services.referral_service import process_referral_submission
        with self.assertRaises(ValidationError) as ctx:
            process_referral_submission(self.ref_code_obj.code, self.referrer)
        self.assertIn("Self-referral", str(ctx.exception))

    def test_same_account_cannot_qualify_twice(self):
        from django.core.exceptions import ValidationError
        from apps.accounts.services.referral_service import (
            process_referral_submission, get_or_create_user_referral_code
        )
        process_referral_submission(self.ref_code_obj.code, self.referred)
        # Second attempt with same referred user
        other_user = User.objects.create_user(
            username='other_referrer',
            email='other@example.com',
            password='TestPassword123!'
        )
        other_code = get_or_create_user_referral_code(other_user)
        with self.assertRaises(ValidationError) as ctx:
            process_referral_submission(other_code.code, self.referred)
        self.assertIn("already redeemed a referral code", str(ctx.exception))

    def test_existing_user_beyond_eligibility_window_rejected(self):
        from datetime import timedelta
        from django.utils import timezone
        from django.core.exceptions import ValidationError
        from apps.accounts.services.referral_service import process_referral_submission
        old_user = User.objects.create_user(
            username='old_user',
            email='old@example.com',
            password='TestPassword123!'
        )
        User.objects.filter(id=old_user.id).update(date_joined=timezone.now() - timedelta(days=30))
        old_user.refresh_from_db()

        with self.assertRaises(ValidationError) as ctx:
            process_referral_submission(self.ref_code_obj.code, old_user)
        self.assertIn("eligibility window", str(ctx.exception))

    def test_replayed_request_idempotency_creates_no_second_reward(self):
        from apps.accounts.services.referral_service import process_referral_submission
        from apps.accounts.models import RewardHistory
        idempotency_key = "test-replay-key-123"
        claim1 = process_referral_submission(self.ref_code_obj.code, self.referred, idempotency_key=idempotency_key)
        self.assertEqual(claim1.status, 'REWARDED')
        initial_reward_count = RewardHistory.objects.count()

        # Replay the exact request
        claim2 = process_referral_submission(self.ref_code_obj.code, self.referred, idempotency_key=idempotency_key)
        self.assertEqual(claim1.id, claim2.id)
        self.assertEqual(RewardHistory.objects.count(), initial_reward_count)

    def test_referral_views_flow(self):
        from apps.accounts.models import ReferralClaim
        self.client.login(username='referred_user', password='TestPassword123!')
        
        # Test GET referrals hub
        hub_res = self.client.get(reverse('referrals'))
        self.assertEqual(hub_res.status_code, 200)
        self.assertContains(hub_res, "Referrals & Friend Rewards")

        # Test POST redeem referral code
        redeem_res = self.client.post(reverse('referrals_redeem'), {'code': self.ref_code_obj.code}, follow=True)
        self.assertEqual(redeem_res.status_code, 200)
        self.assertTrue(ReferralClaim.objects.filter(referred_user=self.referred, status='REWARDED').exists())

