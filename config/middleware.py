# Stage 3/5: Implementation refinement
import time
from collections import defaultdict
from django.http import HttpResponse
from django.conf import settings

# In-memory sliding window rate limiter for login
LOGIN_ATTEMPTS = defaultdict(list)
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX_ATTEMPTS = 5  # max attempts per window per IP/user


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
