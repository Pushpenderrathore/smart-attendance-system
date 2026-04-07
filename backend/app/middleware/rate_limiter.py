"""
Rate Limiting Middleware (no external deps)
────────────────────────────────────────────
✅ Sliding-window counter per IP
✅ Per-route configurable limits
✅ Returns 429 with Retry-After header

Usage:
    @attendance_bp.route("/mark", methods=["POST"])
    @rate_limit(max_requests=5, window_seconds=60)
    def mark_attendance():
        ...
"""
import time
from collections import defaultdict, deque
from functools import wraps
from flask import request, jsonify

# Store: { "route:ip" -> deque of timestamps }
_request_log: dict = defaultdict(deque)


def _get_client_ip() -> str:
    """Get real IP even behind a proxy."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr or "unknown"


def rate_limit(max_requests: int = 10, window_seconds: int = 60):
    """
    Sliding-window rate limiter decorator.

    Args:
        max_requests:   max allowed calls in the window
        window_seconds: rolling window size in seconds
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            ip  = _get_client_ip()
            key = f"{fn.__name__}:{ip}"
            now = time.time()
            log = _request_log[key]

            # Evict timestamps outside the window
            while log and log[0] < now - window_seconds:
                log.popleft()

            if len(log) >= max_requests:
                oldest   = log[0]
                retry_in = int(window_seconds - (now - oldest)) + 1
                resp = jsonify({
                    "error": f"Rate limit exceeded. Max {max_requests} requests per {window_seconds}s.",
                    "retry_after": retry_in,
                })
                resp.status_code = 429
                resp.headers["Retry-After"] = str(retry_in)
                resp.headers["X-RateLimit-Limit"]     = str(max_requests)
                resp.headers["X-RateLimit-Remaining"] = "0"
                return resp

            log.append(now)
            response = fn(*args, **kwargs)

            # Inject rate limit headers into successful responses
            if hasattr(response, "headers"):
                remaining = max_requests - len(log)
                response.headers["X-RateLimit-Limit"]     = str(max_requests)
                response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))

            return response
        return wrapper
    return decorator


# Pre-configured limiters for common use cases
strict    = rate_limit(max_requests=5,  window_seconds=60)    # auth, OTP
standard  = rate_limit(max_requests=30, window_seconds=60)    # normal API
generous  = rate_limit(max_requests=100, window_seconds=60)   # reads
