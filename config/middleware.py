# Stage 1/5: Implementation refinement
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
