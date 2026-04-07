"""
JWT Authentication Service
──────────────────────────
✅ PBKDF2-SHA256 password hashing (stdlib only, no extra deps)
✅ Signed JWT-style tokens (1hr expiry, or custom expiry for refresh)
✅ Role-based access: 'teacher' | 'student'
✅ Token blacklist for logout
"""
import hashlib, hmac, json, os, time, base64, secrets

SECRET_KEY   = os.getenv("SECRET_KEY", "change-me-in-production")
TOKEN_EXPIRY = 3600  # 1 hour

_blacklist: set = set()


def _hash_pw(password: str) -> str:
    salt = "sas_salt_v1"
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 200_000)
    return base64.b64encode(dk).decode()


def _b64e(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64d(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (4 - len(s) % 4))


def _sign(msg: str) -> str:
    return hmac.new(SECRET_KEY.encode(), msg.encode(), hashlib.sha256).hexdigest()


# Default user store (replace with DB queries in production)
_users: dict = {
    "teacher_001": {"name": "Prof. Sharma", "role": "teacher", "password_hash": _hash_pw("teacher123")},
    "teacher_002": {"name": "Dr. Gupta",    "role": "teacher", "password_hash": _hash_pw("gupta456")},
}


def generate_token(user_id: str, role: str, expiry: int = None) -> str:
    """
    Generate a signed JWT.
    expiry: seconds from now. Defaults to TOKEN_EXPIRY (1 hour).
    Pass expiry=7*24*3600 for refresh tokens.
    """
    exp_seconds = expiry if expiry is not None else TOKEN_EXPIRY
    header  = _b64e(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    payload = _b64e(json.dumps({
        "sub": user_id, "role": role,
        "iat": int(time.time()), "exp": int(time.time()) + exp_seconds,
        "jti": secrets.token_hex(8),
    }).encode())
    sig = _b64e(_sign(f"{header}.{payload}").encode())
    return f"{header}.{payload}.{sig}"


def verify_token(token: str) -> tuple:
    """Returns (payload_dict, None) on success or (None, error_msg)."""
    if not token:                         return None, "No token provided."
    if token in _blacklist:               return None, "Token revoked."
    parts = token.split(".")
    if len(parts) != 3:                   return None, "Malformed token."
    header, payload_b64, sig = parts
    if not hmac.compare_digest(sig, _b64e(_sign(f"{header}.{payload_b64}").encode())):
        return None, "Invalid signature."
    try:    payload = json.loads(_b64d(payload_b64))
    except: return None, "Cannot decode token."
    if payload.get("exp", 0) < time.time():
        return None, "Token expired. Please log in again."
    return payload, None


def login(user_id: str, password: str) -> tuple:
    user = _users.get(user_id)
    if not user: return None, "User not found."
    if not hmac.compare_digest(_hash_pw(password), user["password_hash"]):
        return None, "Incorrect password."
    token = generate_token(user_id, user["role"])
    return token, {"id": user_id, "name": user["name"], "role": user["role"]}


def logout(token: str) -> None:
    _blacklist.add(token)


def register_teacher(teacher_id: str, name: str, password: str) -> tuple:
    if teacher_id in _users:
        return False, "Teacher ID already exists."
    _users[teacher_id] = {"name": name, "role": "teacher", "password_hash": _hash_pw(password)}
    return True, "Registered."