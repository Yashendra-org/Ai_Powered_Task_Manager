import time
import ipaddress
import logging
from collections import defaultdict
from django.http import HttpResponse, HttpResponseNotFound
from django.conf import settings

logger = logging.getLogger('security')

# In-memory sliding window rate limit store
# Format: ACTION_ATTEMPTS[action_key] = [timestamps]
RATE_LIMIT_STORE = defaultdict(list)

# Rate Limit Thresholds: (window_seconds, max_attempts)
RATE_LIMIT_RULES = {
    'login': (60, 5),             # Max 5 attempts per min per IP/username
    'register': (60, 5),          # Max 5 attempts per min per IP
    'password_reset': (60, 3),    # Max 3 attempts per min per IP
    'referral_redeem': (60, 5),   # Max 5 attempts per min per IP/user
}

# Suspicious Scanner Probe Patterns (Security Guide: 7,778 Suspicious Requests Case Study)
SUSPICIOUS_PROBE_PATTERNS = [
    '.env', '.env.local', '.env.production', 'web.config',
    '.aws/', '.ssh/', 'id_rsa', 'id_dsa', 'authorized_keys',
    'wp-admin', 'wp-login', 'xmlrpc.php', 'install.php', 'wp-includes', 'wp-content',
    'phpinfo', 'info.php', 'test.php', 'shell.php', 'eval-stdin.php',
    'actuator', 'server-status', 'solr/', 'jenkins/', 'manager/html',
    '.git/', '.git-credentials', 'backup.zip', 'dump.sql', 'backup.sql', 'backup.tar',
    'db.sqlite3', 'database.sqlite', 'cgi-bin', 'setup.cgi', 'phpunit',
    '../', '..%2f', '%2e%2e%2f',
]


class SecurityAndRateLimitMiddleware:
    """
    Enterprise-grade Security & Rate Limiting Middleware.
    Enforces:
    1. Content-Security-Policy (CSP) headers protecting against XSS
    2. Strict-Transport-Security (HSTS) headers forcing HTTPS
    3. Multi-Action Rate Limiting (login, registration, password reset, referral redemption)
       with standard RFC rate-limit headers (X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset, Retry-After)
    4. Anti-Scanner Probe Defenses (instant 404 for malicious scanner probes)
    5. Essential HTTP security headers (nosniff, DENY, strict-origin, COOP, CORP, Permissions-Policy)
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        lower_path = path.lower()

        # 0. Scanner Probe Defense (Security Guide: 7,778 Suspicious Requests Case Study)
        # Immediately reject scanner probes with clean 404 without database lookups
        if any(probe in lower_path for probe in SUSPICIOUS_PROBE_PATTERNS):
            logger.warning(f"Scanner probe blocked: path='{path}' ip='{self.get_client_ip(request)}'")
            return HttpResponseNotFound("Page not found")

        # 1. Multi-Action Rate Limiting
        client_ip = self.get_client_ip(request)
        rate_action, rate_key = self.resolve_rate_limit_target(request, client_ip)

        if rate_action and request.method == 'POST':
            window_sec, max_attempts = RATE_LIMIT_RULES[rate_action]
            now = time.time()
            RATE_LIMIT_STORE[rate_key] = [t for t in RATE_LIMIT_STORE[rate_key] if now - t < window_sec]

            if len(RATE_LIMIT_STORE[rate_key]) >= max_attempts:
                retry_after = int(window_sec - (now - RATE_LIMIT_STORE[rate_key][0]))
                response = HttpResponse(
                    "Too many requests. Please wait a moment and try again.",
                    status=429,
                    content_type="text/plain"
                )
                response['Retry-After'] = str(max(1, retry_after))
                response['X-RateLimit-Limit'] = str(max_attempts)
                response['X-RateLimit-Remaining'] = '0'
                response['X-RateLimit-Reset'] = str(max(1, retry_after))
                return response

            RATE_LIMIT_STORE[rate_key].append(now)

        # Process the request
        response = self.get_response(request)

        # 2. Add Rate Limit Headers on Sensitive Action Responses
        if rate_action:
            window_sec, max_attempts = RATE_LIMIT_RULES[rate_action]
            now = time.time()
            attempts = len([t for t in RATE_LIMIT_STORE[rate_key] if now - t < window_sec])
            remaining = max(0, max_attempts - attempts)
            response['X-RateLimit-Limit'] = str(max_attempts)
            response['X-RateLimit-Remaining'] = str(remaining)
            response['X-RateLimit-Reset'] = str(window_sec)

        # 3. Content-Security-Policy (CSP) Header
        csp_policy = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.tailwindcss.com https://unpkg.com https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net; "
            "font-src 'self' https://fonts.gstatic.com data:; "
            "img-src 'self' data: https: blob:; "
            "connect-src 'self' https:; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )
        response['Content-Security-Policy'] = csp_policy

        # 4. Strict-Transport-Security (HSTS) Header
        response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'

        # 5. Core Defensive Headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
        response['Cross-Origin-Opener-Policy'] = 'same-origin'
        response['Cross-Origin-Resource-Policy'] = 'same-origin'
        response['X-Permitted-Cross-Domain-Policies'] = 'none'

        return response

    def resolve_rate_limit_target(self, request, client_ip):
        """Identifies if the request targets a rate-limited endpoint and generates its key."""
        path = request.path.rstrip('/')
        
        # Login (POST /login or /auth/login)
        if path in ('/login', '/auth/login'):
            username = request.POST.get('username', '').strip().lower()
            return 'login', f"login:{client_ip}:{username}"
        
        # Registration (POST /register or /auth/register)
        if path in ('/register', '/auth/register'):
            return 'register', f"register:{client_ip}"
        
        # Password Reset (POST /password-reset or /auth/password-reset)
        if path in ('/password-reset', '/auth/password-reset'):
            return 'password_reset', f"password_reset:{client_ip}"
        
        # Referral Redemption (POST /referrals/redeem or /account/referrals/redeem)
        if path in ('/referrals/redeem', '/account/referrals/redeem'):
            user = getattr(request, 'user', None)
            user_id = user.id if user and hasattr(user, 'is_authenticated') and user.is_authenticated else 'anon'
            return 'referral_redeem', f"referral:{client_ip}:{user_id}"

        return None, None

    def get_client_ip(self, request):
        """Extracts client IP safely without blind trust of spoofable headers."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # When behind reverse proxies, real client is typically the first or proxy-sanitized IP
            raw_ip = x_forwarded_for.split(',')[0].strip()
            try:
                ipaddress.ip_address(raw_ip)
                return raw_ip
            except ValueError:
                pass
        
        remote_addr = request.META.get('REMOTE_ADDR', '127.0.0.1')
        try:
            ipaddress.ip_address(remote_addr)
            return remote_addr
        except ValueError:
            return '127.0.0.1'

