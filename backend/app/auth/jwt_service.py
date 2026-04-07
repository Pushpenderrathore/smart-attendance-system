"""
JWT Authentication Service
──────────────────────────
✅ PBKDF2-SHA256 password hashing (stdlib only, no extra deps)
✅ Signed JWT-style tokens (1hr expiry)
✅ Role-based access: 'teacher'
✅ Token blacklist for logout
✅ All user data persisted in SQLite — no in-memory dict
"""
import hashlib, hmac, json, os, time, base64, secrets

SECRET_KEY   = os.getenv("SECRET_KEY", "change-me-in-production")
TOKEN_EXPIRY = 3600  # 1 hour

_blacklist: set = set()


# ── Password hashing ───────────────────────────────────────

def _hash_pw(password: str) -> str:
    """PBKDF2-SHA256 with a fixed salt. 200k iterations."""
    salt = "sas_salt_v1"
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 200_000)
    return base64.b64encode(dk).decode()


# ── Base64 helpers ─────────────────────────────────────────

def _b64e(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64d(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (4 - len(s) % 4))


def _sign(msg: str) -> str:
    return hmac.new(SECRET_KEY.encode(), msg.encode(), hashlib.sha256).hexdigest()


# ── Token operations ───────────────────────────────────────

def generate_token(user_id: str, role: str) -> str:
    header  = _b64e(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    payload = _b64e(json.dumps({
        "sub": user_id, "role": role,
        "iat": int(time.time()), "exp": int(time.time()) + TOKEN_EXPIRY,
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


def logout(token: str) -> None:
    _blacklist.add(token)


# ── DB-backed user operations ──────────────────────────────
# Import get_db lazily to avoid circular imports at module load time.

def _get_db():
    from database import get_db
    return get_db()


def login(user_id: str, password: str) -> tuple:
    """
    Returns (token, user_dict) on success or (None, None) on failure.
    Third element is an error string on failure, None on success.
    Matches the call signature expected by auth.py:
        token, result = login(user_id, password)
    So we keep it as a 2-tuple for backward compat:
        (token_or_None, user_dict_or_error_string)
    """
    db = _get_db()
    try:
        row = db.execute(
            "SELECT id, name, role, password_hash FROM teachers WHERE id = ?",
            (user_id,)
        ).fetchone()
    finally:
        db.close()

    if not row:
        return None, "User not found."
    if not hmac.compare_digest(_hash_pw(password), row["password_hash"]):
        return None, "Incorrect password."

    token = generate_token(row["id"], row["role"])
    user  = {"id": row["id"], "name": row["name"], "role": row["role"]}
    return token, user


def register_teacher(teacher_id: str, name: str, password: str) -> tuple:
    """
    Persists a new teacher to the DB.
    Returns (True, "Registered.") or (False, error_message).
    """
    db = _get_db()
    try:
        existing = db.execute(
            "SELECT id FROM teachers WHERE id = ?", (teacher_id,)
        ).fetchone()
        if existing:
            return False, "Teacher ID already exists."

        db.execute(
            "INSERT INTO teachers (id, name, password_hash, role) VALUES (?, ?, ?, 'teacher')",
            (teacher_id, name, _hash_pw(password))
        )
        db.commit()
    finally:
        db.close()

    return True, "Registered."


# ── One-time seed for dev (replaces hardcoded _users) ──────
# Call this from a setup script, NOT on every app start.
# Example:
#   from auth.jwt_service import seed_default_teachers
#   seed_default_teachers()

def seed_default_teachers():
    """
    Seeds the two original hardcoded teachers into the DB.
    Safe to call multiple times — uses INSERT OR IGNORE.
    Run once after creating a fresh database.
    """
    defaults = [
        ("teacher_001", "Prof. Sharma", "teacher123"),
        ("teacher_002", "Dr. Gupta",    "gupta456"),
    ]
    db = _get_db()
    try:
        for tid, name, pw in defaults:
            db.execute(
                "INSERT OR IGNORE INTO teachers (id, name, password_hash, role) VALUES (?, ?, ?, 'teacher')",
                (tid, name, _hash_pw(pw))
            )
        db.commit()
        print(f"[Auth] Seeded {len(defaults)} default teachers.")
    finally:
        db.close()