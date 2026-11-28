import time
import logging
from collections import OrderedDict
from django.http import HttpResponse, HttpResponseNotFound
from django.conf import settings
from config.security import extract_client_ip

logger = logging.getLogger('security')

# Bounded in-memory sliding window rate limit store (prevents OOM DoS)
# Format: RATE_LIMIT_STORE[action_key] = [timestamps]
RATE_LIMIT_STORE = OrderedDict()
MAX_RATE_LIMIT_KEYS = 10000

# Rate Limit Thresholds: (window_seconds, max_attempts)
RATE_LIMIT_RULES = {
    'login': (60, 5),              # Max 5 attempts per min per IP+username
    'login_account': (300, 10),    # Max 10 attempts per 5 min per account across ALL IPs
    'login_ip': (60, 15),          # Max 15 login attempts per min per IP across all usernames
    'register': (60, 5),           # Max 5 registrations per min per IP
    'password_reset': (60, 3),     # Max 3 reset requests per min per IP
    'referral_redeem': (60, 5),    # Max 5 referral redemptions per min per IP/user
    'account_delete': (60, 3),     # Max 3 account deletion attempts per min
    'data_export': (60, 10),       # Max 10 data exports per min
    'api_write': (60, 60),         # Max 60 API mutations per min per IP/user
}

# Suspicious Scanner Probe Patterns (Security Guide: 7,778 Suspicious Requests Case Study)
SUSPICIOUS_PROBE_PATTERNS = (
    '.env', '.env.local', '.env.production', 'web.config',
    '.aws/', '.ssh/', 'id_rsa', 'id_dsa', 'authorized_keys',
    'wp-admin', 'wp-login', 'xmlrpc.php', 'install.php', 'wp-includes', 'wp-content',
    'phpinfo', 'info.php', 'test.php', 'shell.php', 'eval-stdin.php',
    'actuator', 'server-status', 'solr/', 'jenkins/', 'manager/html',
    '.git/', '.git-credentials', '.svn/', '.hg/',
    'backup.zip', 'dump.sql', 'backup.sql', 'backup.tar',
    'db.sqlite3', 'database.sqlite', 'cgi-bin', 'setup.cgi', 'phpunit',
    '../', '..%2f', '%2e%2e%2f', '..\\', '..%5c', '\x00', '%00',
)

ALLOWED_HTTP_METHODS = frozenset({'GET', 'HEAD', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'})

NO_CACHE_PATH_PREFIXES = (
    '/login', '/auth/', '/register', '/logout', '/password-reset',
    '/settings', '/account/', '/profile', '/referrals', '/api/',
    '/dashboard', '/tasks', '/habits', '/assignments', '/notes',
    '/analytics', '/calendar', '/notifications', '/assistant', '/review',
)


def _prune_and_record(key: str, window_sec: int, max_attempts: int, now: float):
    """
    Distributed-ready sliding-window / fixed-bucket rate limiter.
    Uses shared Redis cache across horizontally scaled pods when USE_REDIS_CACHE is active,
    falling back seamlessly to the bounded local OrderedDict store.
    Returns (is_blocked, retry_after_sec, remaining).
    """
    if getattr(settings, 'USE_REDIS_CACHE', False):
        try:
            from django.core.cache import cache
            bucket = int(now // window_sec)
            cache_key = f"rl:{key}:{bucket}"
            if cache.add(cache_key, 1, timeout=window_sec + 5):
                count = 1
            else:
                try:
                    count = cache.incr(cache_key)
                except ValueError:
                    cache.set(cache_key, 1, timeout=window_sec + 5)
                    count = 1
            if count > max_attempts:
                retry_after = max(1, int(((bucket + 1) * window_sec) - now))
                return True, retry_after, 0
            return False, 0, max(0, max_attempts - count)
        except Exception as exc:
            logger.warning(f"Distributed rate-limit cache fallback triggered: {exc}")

    timestamps = [t for t in RATE_LIMIT_STORE.get(key, ()) if now - t < window_sec]

    if len(timestamps) >= max_attempts:
        retry_after = max(1, int(window_sec - (now - timestamps[0])))
        RATE_LIMIT_STORE[key] = timestamps
        RATE_LIMIT_STORE.move_to_end(key)
        return True, retry_after, 0

    timestamps.append(now)
    RATE_LIMIT_STORE[key] = timestamps
    RATE_LIMIT_STORE.move_to_end(key)

    while len(RATE_LIMIT_STORE) > MAX_RATE_LIMIT_KEYS:
        RATE_LIMIT_STORE.popitem(last=False)

    return False, 0, max(0, max_attempts - len(timestamps))


class SecurityAndRateLimitMiddleware:
    """
    Enterprise Defense-in-Depth Security & Rate Limiting Middleware.
    Enforces:
    1. HTTP method allowlisting (blocks TRACE/TRACK/CONNECT)
    2. Anti-Scanner Probe & Path Traversal / Null-byte defense
    3. Multi-Action & Dual-Key Rate Limiting (per-IP + per-account brute force defense)
       with bounded LRU memory safety and RFC rate-limit headers
    4. Content-Security-Policy (CSP), HSTS, Cache-Control, and full browser defense headers
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 0a. Block dangerous/obsolete HTTP methods (TRACE XST, CONNECT proxy abuse)
        if request.method not in ALLOWED_HTTP_METHODS:
            return HttpResponse("Method not allowed", status=405, content_type="text/plain")

        path = request.path
        lower_path = path.lower()
        client_ip = extract_client_ip(request)

        # 0b. Scanner Probe & Path Traversal Defense
        if any(probe in lower_path for probe in SUSPICIOUS_PROBE_PATTERNS):
            logger.warning(f"Scanner probe blocked: path='{path}' ip='{client_ip}'")
            return HttpResponseNotFound("Page not found")

        # 1. Multi-Action & Dual-Key Rate Limiting
        targets = self.resolve_rate_limit_targets(request, client_ip)
        now = time.time()
        primary_header_info = None

        for rate_action, rate_key, on_methods in targets:
            if request.method not in on_methods:
                continue

            window_sec, max_attempts = RATE_LIMIT_RULES[rate_action]
            is_blocked, retry_after, remaining = _prune_and_record(
                rate_key, window_sec, max_attempts, now
            )

            if primary_header_info is None:
                primary_header_info = (max_attempts, remaining, window_sec)

            if is_blocked:
                logger.warning(
                    f"Rate limit exceeded: action='{rate_action}' key='{rate_key}' ip='{client_ip}'"
                )
                response = HttpResponse(
                    "Too many requests. Please wait a moment and try again.",
                    status=429,
                    content_type="text/plain",
                )
                response['Retry-After'] = str(retry_after)
                response['X-RateLimit-Limit'] = str(max_attempts)
                response['X-RateLimit-Remaining'] = '0'
                response['X-RateLimit-Reset'] = str(retry_after)
                return response

        # Process the request
        response = self.get_response(request)

        # 2. Add Rate Limit Headers on Sensitive Action Responses
        if primary_header_info:
            max_attempts, remaining, window_sec = primary_header_info
            response['X-RateLimit-Limit'] = str(max_attempts)
            response['X-RateLimit-Remaining'] = str(remaining)
            response['X-RateLimit-Reset'] = str(window_sec)

        # 3. Cache-Control on Sensitive & Authenticated Routes (Prevents proxy/back-button leak)
        is_authenticated = bool(getattr(getattr(request, 'user', None), 'is_authenticated', False))
        if is_authenticated or any(lower_path.startswith(p) for p in NO_CACHE_PATH_PREFIXES):
            response.setdefault('Cache-Control', 'no-store, no-cache, must-revalidate, private')
            response.setdefault('Pragma', 'no-cache')
            response.setdefault('Expires', '0')

        # 4. Content-Security-Policy (CSP) Header
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.tailwindcss.com https://unpkg.com https://cdn.jsdelivr.net",
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net",
            "font-src 'self' https://fonts.gstatic.com data:",
            "img-src 'self' data: https: blob:",
            "connect-src 'self' https:",
            "object-src 'none'",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'",
        ]
        if not settings.DEBUG and not getattr(settings, 'IS_DEPLOY_CHECK', False):
            csp_directives.append("upgrade-insecure-requests")

        response['Content-Security-Policy'] = "; ".join(csp_directives) + ";"

        # 5. Strict-Transport-Security (HSTS) Header
        if not settings.DEBUG:
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'

        # 6. Core Defensive Headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '0'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=(), payment=(), usb=()'
        response['Cross-Origin-Opener-Policy'] = 'same-origin'
        response['Cross-Origin-Resource-Policy'] = 'same-origin'
        response['X-Permitted-Cross-Domain-Policies'] = 'none'

        return response

    def resolve_rate_limit_targets(self, request, client_ip):
        """Returns list of (rate_action, rate_key, http_methods_set) for the request."""
        path = request.path.rstrip('/')
        targets = []

        if path in ('/login', '/auth/login'):
            username = request.POST.get('username', '').strip().lower()[:150]
            targets.append(('login', f"login:{client_ip}:{username}", {'POST'}))
            if username:
                targets.append(('login_account', f"login_acct:{username}", {'POST'}))
            targets.append(('login_ip', f"login_ip:{client_ip}", {'POST'}))
        elif path in ('/register', '/auth/register'):
            targets.append(('register', f"register:{client_ip}", {'POST'}))
        elif path in ('/password-reset', '/auth/password-reset'):
            targets.append(('password_reset', f"password_reset:{client_ip}", {'POST'}))
        elif path in ('/referrals/redeem', '/account/referrals/redeem'):
            user = getattr(request, 'user', None)
            user_id = user.id if user and getattr(user, 'is_authenticated', False) else 'anon'
            targets.append(('referral_redeem', f"referral:{client_ip}:{user_id}", {'POST'}))
        elif path in ('/delete-account', '/account/delete'):
            user = getattr(request, 'user', None)
            user_id = user.id if user and getattr(user, 'is_authenticated', False) else 'anon'
            targets.append(('account_delete', f"delacct:{client_ip}:{user_id}", {'POST'}))
        elif path.startswith('/settings/export/') or path.startswith('/account/export/') or path.startswith('/habits/export'):
            user = getattr(request, 'user', None)
            user_id = user.id if user and getattr(user, 'is_authenticated', False) else 'anon'
            targets.append(('data_export', f"export:{client_ip}:{user_id}", {'GET'}))
        elif path.startswith('/api/'):
            targets.append(('api_write', f"api:{client_ip}", {'POST', 'PUT', 'PATCH', 'DELETE'}))

        return targets
