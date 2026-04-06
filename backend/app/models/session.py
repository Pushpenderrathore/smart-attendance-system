from flask import Blueprint, jsonify, request
from services.otp_service import generate_otp, refresh_otp, invalidate_otp, get_otp_age
from database import get_db
import time

session_bp = Blueprint("session", __name__)

@session_bp.route("/start", methods=["POST"])
def start_session():
    """Teacher starts a new attendance session."""
    data = request.json or {}

    teacher_id = data.get("teacher_id", "teacher_001")
    subject    = data.get("subject", "Unknown Subject")
    lat        = float(data.get("lat", 28.7041))
    lon        = float(data.get("lon", 77.1025))
    radius     = int(data.get("radius", 100))

    db = get_db()
    cursor = db.cursor()

    # Deactivate previous sessions for this teacher
    cursor.execute(
        "UPDATE sessions SET is_active = 0 WHERE teacher_id = ? AND is_active = 1",
        (teacher_id,)
    )

    # Insert new session
    cursor.execute(
        """INSERT INTO sessions (teacher_id, subject, otp, lat, lon, radius, expires_at)
           VALUES (?, ?, ?, ?, ?, ?, datetime('now', '+1 hour'))""",
        (teacher_id, subject, "", lat, lon, radius)
    )
    session_id = cursor.lastrowid
    db.commit()

    # Generate OTP
    otp = generate_otp(session_id)
    cursor.execute("UPDATE sessions SET otp = ? WHERE id = ?", (otp, session_id))
    db.commit()
    db.close()

    return jsonify({
        "success": True,
        "session_id": session_id,
        "otp": otp,
        "subject": subject,
        "geofence_radius": radius,
        "expires_in_seconds": 60
    }), 201


@session_bp.route("/refresh-otp/<int:session_id>", methods=["POST"])
def refresh_session_otp(session_id):
    """Teacher refreshes OTP for current session."""
    new_otp = refresh_otp(session_id)

    db = get_db()
    db.execute("UPDATE sessions SET otp = ? WHERE id = ?", (new_otp, session_id))
    db.commit()
    db.close()

    return jsonify({
        "success": True,
        "session_id": session_id,
        "otp": new_otp,
        "message": "OTP refreshed successfully"
    })


@session_bp.route("/end/<int:session_id>", methods=["POST"])
def end_session(session_id):
    """Teacher ends the session."""
    invalidate_otp(session_id)

    db = get_db()
    db.execute("UPDATE sessions SET is_active = 0 WHERE id = ?", (session_id,))
    db.commit()
    db.close()

    return jsonify({"success": True, "message": "Session ended."})


@session_bp.route("/status/<int:session_id>", methods=["GET"])
def session_status(session_id):
    """Get current session status."""
    db = get_db()
    session = db.execute(
        "SELECT * FROM sessions WHERE id = ?", (session_id,)
    ).fetchone()
    db.close()

    if not session:
        return jsonify({"error": "Session not found"}), 404

    otp_age = get_otp_age(session_id)

    return jsonify({
        "session_id": session_id,
        "subject": session["subject"],
        "is_active": bool(session["is_active"]),
        "otp_age_seconds": round(otp_age, 1) if otp_age else None,
    })
