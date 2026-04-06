"""
Session Routes (secured)
✅ JWT required for teacher actions
✅ Rate limited
✅ Teacher ID pulled from token (not user input)
"""
from flask import Blueprint, jsonify, request, g
from services.otp_service import generate_otp, refresh_otp, invalidate_otp, get_otp_age, get_attempt_info
from middleware.auth_middleware import require_auth
from middleware.rate_limiter import rate_limit
from database import get_db

session_bp = Blueprint("session", __name__)


@session_bp.route("/start", methods=["POST"])
@require_auth(role="teacher")
@rate_limit(max_requests=10, window_seconds=60)
def start_session():
    data       = request.json or {}
    teacher_id = g.user["sub"]          # from JWT — cannot be spoofed
    subject    = data.get("subject", "Unknown Subject")
    lat        = float(data.get("lat", 28.7041))
    lon        = float(data.get("lon", 77.1025))
    radius     = int(data.get("radius", 100))

    db = get_db()
    db.execute("UPDATE sessions SET is_active=0 WHERE teacher_id=? AND is_active=1", (teacher_id,))
    cursor = db.execute(
        "INSERT INTO sessions (teacher_id, subject, otp, lat, lon, radius, expires_at) "
        "VALUES (?, ?, '', ?, ?, ?, datetime('now','+1 hour'))",
        (teacher_id, subject, lat, lon, radius)
    )
    session_id = cursor.lastrowid
    otp = generate_otp(session_id)
    db.execute("UPDATE sessions SET otp=? WHERE id=?", (otp, session_id))
    db.commit(); db.close()

    return jsonify({
        "success": True, "session_id": session_id,
        "otp": otp, "subject": subject,
        "geofence_radius": radius, "expires_in_seconds": 60
    }), 201


@session_bp.route("/refresh-otp/<int:session_id>", methods=["POST"])
@require_auth(role="teacher")
@rate_limit(max_requests=20, window_seconds=60)
def refresh_session_otp(session_id):
    new_otp = refresh_otp(session_id)
    db = get_db()
    db.execute("UPDATE sessions SET otp=? WHERE id=?", (new_otp, session_id))
    db.commit(); db.close()
    return jsonify({"success": True, "session_id": session_id, "otp": new_otp})


@session_bp.route("/end/<int:session_id>", methods=["POST"])
@require_auth(role="teacher")
def end_session(session_id):
    invalidate_otp(session_id)
    db = get_db()
    db.execute("UPDATE sessions SET is_active=0 WHERE id=?", (session_id,))
    db.commit(); db.close()
    return jsonify({"success": True, "message": "Session ended."})


@session_bp.route("/status/<int:session_id>", methods=["GET"])
@require_auth(role="teacher")
def session_status(session_id):
    db = get_db()
    session = db.execute("SELECT * FROM sessions WHERE id=?", (session_id,)).fetchone()
    db.close()
    if not session:
        return jsonify({"error": "Session not found"}), 404
    age = get_otp_age(session_id)
    attempts = get_attempt_info(session_id)
    return jsonify({
        "session_id": session_id, "subject": session["subject"],
        "is_active": bool(session["is_active"]),
        "otp_age_seconds": round(age, 1) if age else None,
        "otp_attempts": attempts,
    })
