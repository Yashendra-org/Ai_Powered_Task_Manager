import time
import logging
from collections import defaultdict
from django.http import HttpResponse, HttpResponseNotFound
from django.conf import settings

logger = logging.getLogger('security')

# In-memory sliding window rate limiter for login
LOGIN_ATTEMPTS = defaultdict(list)
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX_ATTEMPTS = 5  # max attempts per window per IP/user

# Suspicious Scanner Probe Patterns (Security Guide: 7,778 Suspicious Requests Case Study)
SUSPICIOUS_PROBE_PATTERNS = [
    '.env', '.aws/', '.ssh/', 'id_rsa',
    'wp-admin', 'wp-login', 'xmlrpc.php', 'install.php',
    'phpinfo', 'actuator', 'server-status',
    '.git/', '.git-credentials', 'backup.zip', 'dump.sql',
]


class SecurityAndRateLimitMiddleware:
    """
    Enterprise-grade Security & Rate Limiting Middleware.
    Enforces:
    1. Content-Security-Policy (CSP) headers protecting against XSS
    2. Strict-Transport-Security (HSTS) headers forcing HTTPS
    3. Brute-force rate limiting on /login/ with standard headers
       (X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset)
    4. Essential HTTP security headers (X-Content-Type-Options, X-Frame-Options, Referrer-Policy)
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        # 0. Scanner Probe Defense (Security Guide: 7,778 Suspicious Requests Case Study)
        # Immediately reject scanner probes with clean 404 without database lookups
        lower_path = path.lower()
        if any(probe in lower_path for probe in SUSPICIOUS_PROBE_PATTERNS):
            logger.warning(f"Scanner probe blocked: path='{path}' ip='{self.get_client_ip(request)}'")
            return HttpResponseNotFound("Page not found")

        # 1. Rate Limiting on Login Endpoint (POST /login/)
        is_login_post = path.rstrip('/') == '/login' and request.method == 'POST'
        client_ip = self.get_client_ip(request)
        username = request.POST.get('username', '').strip().lower()
        rate_key = f"{client_ip}:{username}"

        if is_login_post:
            now = time.time()
            LOGIN_ATTEMPTS[rate_key] = [t for t in LOGIN_ATTEMPTS[rate_key] if now - t < RATE_LIMIT_WINDOW]

            if len(LOGIN_ATTEMPTS[rate_key]) >= RATE_LIMIT_MAX_ATTEMPTS:
                retry_after = int(RATE_LIMIT_WINDOW - (now - LOGIN_ATTEMPTS[rate_key][0]))
                response = HttpResponse(
                    "Too many login attempts. Please wait a minute and try again.",
                    status=429,
                    content_type="text/plain"
                )
                response['Retry-After'] = str(max(1, retry_after))
                response['X-RateLimit-Limit'] = str(RATE_LIMIT_MAX_ATTEMPTS)
                response['X-RateLimit-Remaining'] = '0'
                response['X-RateLimit-Reset'] = str(max(1, retry_after))
                return response

            LOGIN_ATTEMPTS[rate_key].append(now)

        # Process the request
        response = self.get_response(request)

        # 2. Add Rate Limit Headers on Login Responses
        if path.rstrip('/') == '/login':
            now = time.time()
            attempts = len([t for t in LOGIN_ATTEMPTS[rate_key] if now - t < RATE_LIMIT_WINDOW])
            remaining = max(0, RATE_LIMIT_MAX_ATTEMPTS - attempts)
            response['X-RateLimit-Limit'] = str(RATE_LIMIT_MAX_ATTEMPTS)
            response['X-RateLimit-Remaining'] = str(remaining)
            response['X-RateLimit-Reset'] = str(RATE_LIMIT_WINDOW)

        # 3. Content-Security-Policy (CSP) Header
        # Whitelists self, inline scripts for Chart.js/Alpine, and required CDNs
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

        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '127.0.0.1')
