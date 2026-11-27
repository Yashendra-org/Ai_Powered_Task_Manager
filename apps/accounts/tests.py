from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.tasks.models import Task

User = get_user_model()


class AuthenticationAndDashboardTests(TestCase):
    def setUp(self):
        from config.middleware import RATE_LIMIT_STORE
        RATE_LIMIT_STORE.clear()
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


class ProfessionalUrlRoutingTests(TestCase):
    """
    Verifies that modern enterprise semantic URL routes and legacy aliases
    resolve and function seamlessly across all modules.
    """
    def setUp(self):
        from config.middleware import RATE_LIMIT_STORE
        RATE_LIMIT_STORE.clear()
        self.client = Client()
        self.user = User.objects.create_user(
            username='url_test_user',
            email='url_test@example.com',
            password='TestPassword123!'
        )
        from apps.assignments.models import Subject
        Subject.objects.create(user=self.user, name="Computer Science", code="CS101")

    def test_public_auth_routes(self):
        # Professional /auth/ namespace
        res_auth_login = self.client.get('/auth/login/')
        self.assertEqual(res_auth_login.status_code, 200)
        res_auth_reg = self.client.get('/auth/register/')
        self.assertEqual(res_auth_reg.status_code, 200)

        # Legacy routes remain functional
        res_login = self.client.get('/login/')
        self.assertEqual(res_login.status_code, 200)
        res_reg = self.client.get('/register/')
        self.assertEqual(res_reg.status_code, 200)

    def test_authenticated_account_routes(self):
        self.client.login(username='url_test_user', password='TestPassword123!')
        
        # /account/ namespace
        self.assertEqual(self.client.get('/account/settings/').status_code, 200)
        self.assertEqual(self.client.get('/account/profile/').status_code, 200)
        self.assertEqual(self.client.get('/account/referrals/').status_code, 200)

        # Legacy aliases
        self.assertEqual(self.client.get('/settings/').status_code, 200)
        self.assertEqual(self.client.get('/profile/').status_code, 200)
        self.assertEqual(self.client.get('/referrals/').status_code, 200)

    def test_productivity_and_intelligence_routes(self):
        self.client.login(username='url_test_user', password='TestPassword123!')

        # Tasks
        self.assertEqual(self.client.get('/tasks/').status_code, 200)
        self.assertEqual(self.client.get('/tasks/my-day/').status_code, 200)
        self.assertEqual(self.client.get('/tasks/today/').status_code, 200)
        self.assertEqual(self.client.get('/tasks/new/').status_code, 200)
        self.assertEqual(self.client.get('/tasks/create/').status_code, 200)

        # Assignments
        self.assertEqual(self.client.get('/assignments/').status_code, 200)
        self.assertEqual(self.client.get('/assignments/new/').status_code, 200)
        self.assertEqual(self.client.get('/assignments/create/').status_code, 200)
        self.assertEqual(self.client.get('/assignments/professors/').status_code, 200)
        self.assertEqual(self.client.get('/assignments/teachers/').status_code, 200)

        # Habits
        self.assertEqual(self.client.get('/habits/').status_code, 200)
        self.assertEqual(self.client.get('/habits/new/').status_code, 200)
        self.assertEqual(self.client.get('/habits/create/').status_code, 200)

        # Notes
        self.assertEqual(self.client.get('/notes/').status_code, 200)
        self.assertEqual(self.client.get('/notes/new/').status_code, 200)
        self.assertEqual(self.client.get('/notes/create/').status_code, 200)

        # Analytics & AI
        self.assertEqual(self.client.get('/analytics/').status_code, 200)
        self.assertEqual(self.client.get('/analytics/overview/').status_code, 200)
        self.assertEqual(self.client.get('/ai/assistant/').status_code, 200)
        self.assertEqual(self.client.get('/assistant/').status_code, 200)
        self.assertEqual(self.client.get('/ai/review/').status_code, 200)
        self.assertEqual(self.client.get('/review/').status_code, 200)

        # Notifications
        self.assertEqual(self.client.get('/notifications/').status_code, 200)
        self.assertEqual(self.client.get('/notifications/inbox/').status_code, 200)


class HardenedSecurityTests(TestCase):
    """
    Tests security protections:
    - Probe scanner defense
    - Multi-endpoint rate limiting
    - Timing attack equalization
    - Defensive headers
    - Bounds validation
    """
    def setUp(self):
        from config.middleware import RATE_LIMIT_STORE
        RATE_LIMIT_STORE.clear()
        self.client = Client()

    def test_scanner_probe_blocked(self):
        probes = [
            '/.env',
            '/admin/.env.local',
            '/wp-login.php',
            '/actuator/health',
            '/dump.sql',
            '/.git/config',
            '/phpinfo.php',
            '/backup.zip',
        ]
        for probe in probes:
            response = self.client.get(probe)
            self.assertEqual(response.status_code, 404, f"Probe {probe} should be rejected with 404")

    def test_multi_endpoint_rate_limiting(self):
        # 1. Login rate limiting
        for _ in range(5):
            self.client.post('/auth/login/', {'username': 'attacker', 'password': 'bad'}, REMOTE_ADDR='198.51.100.1')
        blocked_res = self.client.post('/auth/login/', {'username': 'attacker', 'password': 'bad'}, REMOTE_ADDR='198.51.100.1')
        self.assertEqual(blocked_res.status_code, 429)
        self.assertIn('Retry-After', blocked_res.headers)
        self.assertEqual(blocked_res.headers.get('X-RateLimit-Remaining'), '0')

        # 2. Registration rate limiting
        for _ in range(5):
            self.client.post('/auth/register/', {'username': 'spammer'}, REMOTE_ADDR='198.51.100.2')
        blocked_reg = self.client.post('/auth/register/', {'username': 'spammer'}, REMOTE_ADDR='198.51.100.2')
        self.assertEqual(blocked_reg.status_code, 429)

    def test_authentication_timing_attack_protection(self):
        from apps.accounts.backends import EmailOrUsernameModelBackend
        backend = EmailOrUsernameModelBackend()
        # Authenticating a non-existent user should invoke dummy hasher and return None safely
        result = backend.authenticate(request=None, username='completely_non_existent_user_99999', password='AnyPassword123!')
        self.assertIsNone(result)

    def test_security_defensive_headers_present(self):
        res = self.client.get('/login/')
        self.assertEqual(res.status_code, 200)
        self.assertIn('Content-Security-Policy', res.headers)
        self.assertIn('Strict-Transport-Security', res.headers)
        self.assertEqual(res.headers.get('X-Content-Type-Options'), 'nosniff')
        self.assertEqual(res.headers.get('X-Frame-Options'), 'DENY')
        self.assertEqual(res.headers.get('Cross-Origin-Opener-Policy'), 'same-origin')
        self.assertEqual(res.headers.get('Cross-Origin-Resource-Policy'), 'same-origin')
        self.assertEqual(res.headers.get('X-Permitted-Cross-Domain-Policies'), 'none')

    def test_note_content_bounds_validation(self):
        from apps.notes.forms import NoteForm
        oversized_content = "X" * 50001
        form = NoteForm(data={'title': 'Large Note', 'content': oversized_content})
        self.assertFalse(form.is_valid())
        self.assertIn('content', form.errors)


class DataPortabilityAndAuditTests(TestCase):
    """
    Pillar 2, #8: Self-Service Data Portability & GDPR Exporter Tests
    Pillar 3, #10: Structured Security Audit Trail Tests
    Pillar 5, #18: PWA Offline Fallback Tests
    """
    def setUp(self):
        from config.middleware import RATE_LIMIT_STORE
        RATE_LIMIT_STORE.clear()
        self.client = Client()
        self.user = User.objects.create_user(
            username='exporter_user',
            email='export@example.com',
            password='Password123!',
            timezone='Asia/Kolkata'
        )
        self.client.login(username='exporter_user', password='Password123!')
        self.task = Task.objects.create(
            user=self.user,
            title='Exportable Task Item',
            priority='high',
            estimated_duration=45
        )

    def test_export_json_payload_and_audit(self):
        response = self.client.get(reverse('export_data_json'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertIn('attachment; filename="habittracker_backup_', response['Content-Disposition'])

        data = response.json()
        self.assertEqual(data['metadata']['user']['username'], 'exporter_user')
        self.assertEqual(len(data['tasks']), 1)
        self.assertEqual(data['tasks'][0]['title'], 'Exportable Task Item')

        # Verify audit log was recorded
        audit = self.user.audit_logs.filter(action='EXPORT_JSON').first()
        self.assertIsNotNone(audit)
        self.assertIn('JSON format', audit.description)

    def test_export_csv_payload_and_audit(self):
        response = self.client.get(reverse('export_data_csv'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response['Content-Type'].startswith('text/csv'))
        self.assertIn('attachment; filename="habittracker_tasks_', response['Content-Disposition'])

        content = response.content.decode('utf-8')
        self.assertIn('Title,Description,Category,Priority,Status', content)
        self.assertIn('Exportable Task Item', content)

        # Verify audit log
        audit = self.user.audit_logs.filter(action='EXPORT_CSV').first()
        self.assertIsNotNone(audit)

    def test_export_ics_payload_and_audit(self):
        # Create a task with due_at
        from django.utils import timezone
        Task.objects.create(
            user=self.user,
            title='Calendar Synced Exam',
            due_at=timezone.now() + timezone.timedelta(days=1),
            estimated_duration=60,
            priority='high'
        )
        response = self.client.get(reverse('export_data_ics'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response['Content-Type'].startswith('text/calendar'))
        self.assertIn('attachment; filename="habittracker_schedule_', response['Content-Disposition'])

        content = response.content.decode('utf-8')
        self.assertIn('BEGIN:VCALENDAR', content)
        self.assertIn('BEGIN:VEVENT', content)
        self.assertIn('SUMMARY:Calendar Synced Exam', content)
        self.assertIn('END:VCALENDAR', content)

        # Verify audit log
        audit = self.user.audit_logs.filter(action='EXPORT_ICS').first()
        self.assertIsNotNone(audit)

    def test_exports_require_authentication(self):
        self.client.logout()
        for endpoint in ['export_data_json', 'export_data_csv', 'export_data_ics']:
            res = self.client.get(reverse(endpoint))
            self.assertEqual(res.status_code, 302)
            self.assertTrue(res.url.startswith('/login/'))

    def test_pwa_offline_fallback_page_renders(self):
        response = self.client.get('/offline/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'offline.html')
        self.assertContains(response, "You're Currently Offline")


class PenetrationSecurityRegressionTests(TestCase):
    """
    Senior Cybersecurity Audit Regression Suite:
    Verifies defense against X-Forwarded-For IP spoofing, per-account brute force,
    Open Redirects (HTTP_REFERER), CSV/ICS formula & CRLF injection, Logout CSRF,
    Malicious file upload magic-byte spoofing, HTTP TRACE method blocking,
    Host header poisoning, and unhandled query parameter DoS crashes.
    """
    def setUp(self):
        from config.middleware import RATE_LIMIT_STORE
        RATE_LIMIT_STORE.clear()
        self.client = Client()
        self.user = User.objects.create_user(
            username='sec_victim',
            email='sec_victim@example.com',
            password='StrongPassword123!'
        )

    def test_xff_header_spoofing_does_not_bypass_rate_limit(self):
        # Attacker sends rotating X-Forwarded-For headers from the same connection IP
        for i in range(5):
            self.client.post(
                '/auth/login/',
                {'username': 'sec_victim', 'password': 'WrongPassword'},
                REMOTE_ADDR='198.51.100.44',
                HTTP_X_FORWARDED_FOR=f'203.0.113.{i}'
            )
        blocked = self.client.post(
            '/auth/login/',
            {'username': 'sec_victim', 'password': 'WrongPassword'},
            REMOTE_ADDR='198.51.100.44',
            HTTP_X_FORWARDED_FOR='203.0.113.99'
        )
        self.assertEqual(blocked.status_code, 429)

    def test_per_account_distributed_brute_force_blocked(self):
        # Rotating client IPs targeting a single victim account must still trigger lockout
        for i in range(10):
            res = self.client.post(
                '/auth/login/',
                {'username': 'sec_victim', 'password': f'Guess{i}'},
                REMOTE_ADDR=f'198.51.100.{10 + i}'
            )
            self.assertNotEqual(res.status_code, 429)

        blocked = self.client.post(
            '/auth/login/',
            {'username': 'sec_victim', 'password': 'Guess11'},
            REMOTE_ADDR='198.51.100.250'
        )
        self.assertEqual(blocked.status_code, 429)

    def test_open_redirect_via_referer_blocked(self):
        self.client.login(username='sec_victim', password='StrongPassword123!')
        task = Task.objects.create(user=self.user, title='Safe Redirect Task')
        res = self.client.post(
            reverse('task_toggle', kwargs={'task_id': task.id}),
            HTTP_REFERER='https://evil-phishing-domain.com/login'
        )
        self.assertEqual(res.status_code, 302)
        self.assertFalse(res.url.startswith('https://evil-phishing-domain.com'))

    def test_csv_formula_injection_neutralized(self):
        self.client.login(username='sec_victim', password='StrongPassword123!')
        Task.objects.create(user=self.user, title='=cmd|\'/C calc\'!A0')
        Task.objects.create(user=self.user, title='+SUM(1+1)')
        res = self.client.get(reverse('export_data_csv'))
        self.assertEqual(res.status_code, 200)
        body = res.content.decode('utf-8')
        self.assertIn("'=cmd|'/C calc'!A0", body)
        self.assertIn("'+SUM(1+1)", body)

    def test_ics_crlf_injection_and_json_assignment_export_safe(self):
        from apps.assignments.models import Subject, Assignment
        from django.utils import timezone
        self.client.login(username='sec_victim', password='StrongPassword123!')
        subj = Subject.objects.create(user=self.user, name='Security 101', code='SEC101')
        Assignment.objects.create(
            user=self.user,
            subject=subj,
            title='Assignment Serialization Test',
            due_at=timezone.now() + timezone.timedelta(days=1)
        )
        Task.objects.create(
            user=self.user,
            title="Evil\r\nBEGIN:VALARM\r\nACTION:DISPLAY",
            due_at=timezone.now() + timezone.timedelta(hours=3)
        )
        ics_res = self.client.get(reverse('export_data_ics'))
        self.assertEqual(ics_res.status_code, 200)
        ics_text = ics_res.content.decode('utf-8')
        self.assertNotIn("\nBEGIN:VALARM", ics_text)

        json_res = self.client.get(reverse('export_data_json'))
        self.assertEqual(json_res.status_code, 200)
        self.assertEqual(json_res.json()['assignments'][0]['subject'], 'Security 101')

    def test_logout_requires_post_to_prevent_csrf(self):
        self.client.login(username='sec_victim', password='StrongPassword123!')
        get_res = self.client.get(reverse('logout'))
        self.assertEqual(get_res.status_code, 405)
        post_res = self.client.post(reverse('logout'))
        self.assertEqual(post_res.status_code, 302)

    def test_dangerous_http_trace_method_blocked(self):
        res = self.client.generic('TRACE', '/login/')
        self.assertEqual(res.status_code, 405)

    def test_calendar_and_filter_invalid_params_do_not_crash_500(self):
        self.client.login(username='sec_victim', password='StrongPassword123!')
        self.assertEqual(self.client.get('/calendar/?year=abc&month=xyz').status_code, 200)
        self.assertEqual(self.client.get('/calendar/?year=99999999&month=5').status_code, 200)
        self.assertEqual(self.client.get('/tasks/?category=not_an_int').status_code, 200)
        self.assertEqual(self.client.get('/assignments/?subject=not_an_int').status_code, 200)

    def test_malicious_spoofed_pdf_magic_bytes_rejected(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from apps.assignments.forms import AssignmentForm
        from apps.assignments.models import Subject
        subj = Subject.objects.create(user=self.user, name='AppSec', code='AS101')
        spoofed_file = SimpleUploadedFile('evil.pdf', b'<script>alert(1)</script>', content_type='application/pdf')
        form = AssignmentForm(
            data={
                'title': 'Malicious Upload',
                'subject': subj.id,
                'due_at': '2026-12-01T12:00',
                'priority': 'high',
                'status': 'not_started',
            },
            files={'attachment': spoofed_file},
            user=self.user,
        )
        self.assertFalse(form.is_valid())
        self.assertIn('attachment', form.errors)





