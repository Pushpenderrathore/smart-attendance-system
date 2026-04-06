import random
import time
import string

# In-memory store: { session_id: { otp, timestamp } }
otp_store: dict = {}

def generate_otp(session_id: int, length: int = 6) -> str:
    """Generate a numeric OTP and bind it to a session."""
    otp = "".join(random.choices(string.digits, k=length))
    otp_store[session_id] = {
        "otp": otp,
        "timestamp": time.time()
    }
    return otp

def verify_otp(session_id: int, user_otp: str, expiry: int = 60) -> tuple[bool, str]:
    """
    Verify OTP for a session.
    Returns (is_valid: bool, message: str)
    """
    if session_id not in otp_store:
        return False, "No active session found for this ID."

    data = otp_store[session_id]
    elapsed = time.time() - data["timestamp"]

    if elapsed > expiry:
        del otp_store[session_id]
        return False, f"OTP expired ({int(elapsed)}s ago). Ask teacher to refresh."

    if data["otp"] != user_otp.strip():
        return False, "Invalid OTP. Please check and try again."

    return True, "OTP verified successfully."

def refresh_otp(session_id: int, length: int = 6) -> str:
    """Generate a new OTP for an existing session (teacher refresh)."""
    return generate_otp(session_id, length)

def invalidate_otp(session_id: int) -> None:
    """Remove OTP when session ends."""
    otp_store.pop(session_id, None)

def get_otp_age(session_id: int) -> float | None:
    """Returns seconds since OTP was generated, or None if not found."""
    if session_id not in otp_store:
        return None
    return time.time() - otp_store[session_id]["timestamp"]
