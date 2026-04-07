"""
Auth Routes
───────────
POST /auth/login    → { token, user }
POST /auth/logout   → blacklists token
POST /auth/register → register new teacher
GET  /auth/me       → current user info
"""
from flask import Blueprint, request, jsonify, g
from auth.jwt_service import login, logout, register_teacher
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

    return jsonify({
        "success":    True,
        "token":      token,
        "user":       result,
        "expires_in": 3600,
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