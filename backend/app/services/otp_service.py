"""
Secure OTP Service
──────────────────
✅ OTPs stored as SHA-256 hashes (never plaintext)
✅ Max 3 attempts per session before lockout
✅ Lockout lasts 60 seconds
✅ Constant-time comparison (timing attack safe)
"""

import hashlib
import hmac
import time
import random
import string

_otp_store: dict = {}

MAX_ATTEMPTS = 3
LOCK_SECONDS = 60
OTP_LENGTH   = 6


def _hash_otp(otp: str) -> str:
    return hashlib.sha256(otp.encode()).hexdigest()


def _safe_compare(a: str, b: str) -> bool:
    return hmac.compare_digest(a, b)


def generate_otp(session_id: int, length: int = OTP_LENGTH) -> str:
    """Generate OTP, store its HASH only. Returns raw OTP once."""
    otp = "".join(random.choices(string.digits, k=length))
    _otp_store[session_id] = {
        "hash":      _hash_otp(otp),
        "timestamp": time.time(),
        "attempts":  0,
        "locked_at": None,
    }
    return otp


def verify_otp(session_id: int, user_otp: str, expiry: int = 60) -> tuple:
    """
    Verify with lockout + expiry + constant-time hash compare.
    Returns (is_valid: bool, message: str)
    """
    if session_id not in _otp_store:
        return False, "No active session found."

    entry = _otp_store[session_id]
    now   = time.time()

    # Lockout check
    if entry["locked_at"] is not None:
        elapsed = now - entry["locked_at"]
        if elapsed < LOCK_SECONDS:
            return False, f"Too many failed attempts. Retry in {int(LOCK_SECONDS - elapsed)}s."
        entry["attempts"]  = 0
        entry["locked_at"] = None

    # Expiry check
    age = now - entry["timestamp"]
    if age > expiry:
        del _otp_store[session_id]
        return False, f"OTP expired ({int(age)}s old). Ask teacher to refresh."

    # Constant-time hash compare
    if not _safe_compare(_hash_otp(user_otp.strip()), entry["hash"]):
        entry["attempts"] += 1
        left = MAX_ATTEMPTS - entry["attempts"]
        if entry["attempts"] >= MAX_ATTEMPTS:
            entry["locked_at"] = now
            return False, f"Too many wrong attempts. Locked for {LOCK_SECONDS}s."
        return False, f"Invalid OTP. {left} attempt(s) left."

    entry["attempts"] = 0
    return True, "OTP verified."


def refresh_otp(session_id: int) -> str:
    return generate_otp(session_id)


def invalidate_otp(session_id: int) -> None:
    _otp_store.pop(session_id, None)


def get_otp_age(session_id: int):
    if session_id not in _otp_store:
        return None
    return time.time() - _otp_store[session_id]["timestamp"]


def get_attempt_info(session_id: int) -> dict:
    if session_id not in _otp_store:
        return {"attempts": 0, "locked": False}
    e = _otp_store[session_id]
    return {"attempts": e["attempts"], "locked": e["locked_at"] is not None}
