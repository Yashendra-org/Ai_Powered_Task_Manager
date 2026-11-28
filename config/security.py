"""
Shared Security Utilities (Defense-in-Depth).
Centralizes IP extraction (anti-spoofing), open-redirect prevention,
and CSV/Excel formula injection sanitization.
"""
import ipaddress
from django.conf import settings
from django.shortcuts import redirect
from django.utils.http import url_has_allowed_host_and_scheme


def extract_client_ip(request) -> str:
    """
    Safely extracts the client IP address without blindly trusting spoofable headers.
    Only honors X-Forwarded-For when running behind a trusted reverse proxy
    (IS_RENDER or TRUST_PROXY_HEADERS=True).
    """
    if not request:
        return "127.0.0.1"

    trust_proxy = getattr(settings, "IS_RENDER", False) or getattr(settings, "TRUST_PROXY_HEADERS", False)
    if trust_proxy:
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            raw_ip = x_forwarded_for.split(",")[0].strip()
            try:
                ipaddress.ip_address(raw_ip)
                return raw_ip
            except ValueError:
                pass

    remote_addr = request.META.get("REMOTE_ADDR", "127.0.0.1")
    try:
        ipaddress.ip_address(remote_addr)
        return remote_addr
    except ValueError:
        return "127.0.0.1"


def safe_redirect_back(request, fallback_url_name: str):
    """
    Safely redirects to HTTP_REFERER only if it passes Django's host & scheme check.
    Prevents Open Redirect / Phishing via Referer header poisoning.
    """
    referer = request.META.get("HTTP_REFERER")
    if referer and url_has_allowed_host_and_scheme(
        url=referer,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(referer)
    return redirect(fallback_url_name)


def sanitize_csv_cell(value) -> str:
    """
    Neutralizes CSV / Spreadsheet Formula Injection (DDE / CWE-1236) by prefixing
    cells beginning with formula triggers (=, +, -, @, tab, CR) with a single quote.
    """
    if value is None:
        return ""
    text = str(value)
    if not text:
        return ""
    stripped = text.lstrip(" ")
    if text[0] in ("=", "+", "-", "@", "\t", "\r") or (stripped and stripped[0] in ("=", "+", "-", "@")):
        return f"'{text}"
    return text


def clamp_search_query(raw_query: str, max_len: int = 100) -> str:
    """Normalize and bound free-text search queries to protect DB LIKE/icontains scans."""
    return (raw_query or "").strip()[:max_len]
