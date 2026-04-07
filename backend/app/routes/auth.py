"""
Auth Routes
───────────
POST /auth/login    → access_token + refresh_token
POST /auth/refresh  → new access_token (using refresh_token)
POST /auth/logout   → blacklists token
POST /auth/register → register new teacher
GET  /auth/me       → current user info
"""
from flask import Blueprint, request, jsonify, g
from auth.jwt_service import login, logout, register_teacher, verify_token, generate_token
from middleware.auth_middleware import require_auth
from middleware.rate_limiter import rate_limit

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["POST"])
@rate_limit(max_requests=5, window_seconds=60)
def do_login():
    data     = request.json or {}
    user_id  = data.get("user_id", "").strip()
    password = data.get("password", "")

    if not user_id or not password:
        return jsonify({"error": "user_id and password are required."}), 400

    token, result = login(user_id, password)
    if not token:
        return jsonify({"error": result}), 401

    # Generate refresh token (7-day expiry) alongside the access token
    refresh = generate_token(result["id"], result["role"], expiry=7 * 24 * 3600)

    return jsonify({
        "success":            True,
        "user":               result,
        "access_token":       token,
        "refresh_token":      refresh,
        "token_type":         "Bearer",
        "expires_in":         3600,
        "refresh_expires_in": 7 * 24 * 3600,
    })


@auth_bp.route("/refresh", methods=["POST"])
@rate_limit(max_requests=10, window_seconds=60)
def do_refresh():
    """Exchange a valid refresh token for a new access + refresh pair."""
    data          = request.json or {}
    refresh_token = data.get("refresh_token", "")

    if not refresh_token:
        return jsonify({"error": "refresh_token is required."}), 400

    payload, err = verify_token(refresh_token)
    if err:
        return jsonify({"error": f"Invalid refresh token: {err}"}), 401

    # Issue new access token
    new_access = generate_token(payload["sub"], payload["role"], expiry=3600)
    # Rotate: blacklist old refresh token, issue new one
    logout(refresh_token)
    new_refresh = generate_token(payload["sub"], payload["role"], expiry=7 * 24 * 3600)

    return jsonify({
        "success":            True,
        "access_token":       new_access,
        "refresh_token":      new_refresh,
        "token_type":         "Bearer",
        "expires_in":         3600,
        "refresh_expires_in": 7 * 24 * 3600,
    })


@auth_bp.route("/logout", methods=["POST"])
@require_auth()
def do_logout():
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.split(" ", 1)[1] if " " in auth_header else ""
    logout(token)
    return jsonify({"success": True, "message": "Logged out."})


@auth_bp.route("/register", methods=["POST"])
@rate_limit(max_requests=3, window_seconds=300)
def do_register():
    data       = request.json or {}
    teacher_id = data.get("teacher_id", "").strip()
    name       = data.get("name", "").strip()
    password   = data.get("password", "")

    if not all([teacher_id, name, password]):
        return jsonify({"error": "teacher_id, name, and password are required."}), 400

    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters."}), 400

    ok, msg = register_teacher(teacher_id, name, password)
    if not ok:
        return jsonify({"error": msg}), 409

    return jsonify({"success": True, "message": msg}), 201


@auth_bp.route("/me", methods=["GET"])
@require_auth()
def me():
    return jsonify({"user": g.user})
    