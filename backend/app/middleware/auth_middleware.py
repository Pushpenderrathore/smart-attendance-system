"""
Auth Middleware
───────────────
Decorators to protect Flask routes with JWT + role checks.

Usage:
    @session_bp.route("/start", methods=["POST"])
    @require_auth(role="teacher")
    def start_session():
        teacher_id = g.user["sub"]
        ...
"""
from functools import wraps
from flask import request, jsonify, g
from auth.jwt_service import verify_token


def require_auth(role: str = None):
    """
    Decorator factory. Validates Bearer token in Authorization header.
    Sets g.user = payload dict on success.
    Optionally enforces a required role ('teacher' | 'student').
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                return jsonify({"error": "Missing or invalid Authorization header."}), 401

            token = auth_header.split(" ", 1)[1]
            payload, err = verify_token(token)
            if err:
                return jsonify({"error": err}), 401

            if role and payload.get("role") != role:
                return jsonify({"error": f"Access denied. Required role: {role}"}), 403

            g.user = payload
            return fn(*args, **kwargs)
        return wrapper
    return decorator
