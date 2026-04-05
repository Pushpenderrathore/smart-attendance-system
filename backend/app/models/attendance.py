from flask import Blueprint, jsonify, request
from services.otp_service import verify_otp
from services.geo_service import validate_location, is_plausible_location
from services.anomaly_detection import (
    detect_duplicate_device,
    detect_coordinate_clustering,
    score_risk
)
from database import get_db

attendance_bp = Blueprint("attendance", __name__)

@attendance_bp.route("/mark", methods=["POST"])
def mark_attendance():
    """Student submits attendance with OTP + GPS."""
    data = request.json

    # --- Input Validation ---
    required = ["session_id", "otp", "lat", "lon", "student_id", "student_name", "device_id"]
    for field in required:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    session_id   = int(data["session_id"])
    otp          = data["otp"]
    lat          = float(data["lat"])
    lon          = float(data["lon"])
    student_id   = data["student_id"].strip()
    student_name = data["student_name"].strip()
    device_id    = data["device_id"].strip()

    db = get_db()

    # --- Fetch Session ---
    session = db.execute(
        "SELECT * FROM sessions WHERE id = ? AND is_active = 1", (session_id,)
    ).fetchone()

    if not session:
        db.close()
        return jsonify({"error": "Session not found or already closed."}), 404

    # --- OTP Verification ---
    from config import OTP_EXPIRY_SECONDS
    otp_valid, otp_msg = verify_otp(session_id, otp, expiry=OTP_EXPIRY_SECONDS)
    if not otp_valid:
        db.close()
        return jsonify({"error": otp_msg}), 400

    # --- Duplicate Student Check ---
    already = db.execute(
        "SELECT id FROM attendance WHERE session_id = ? AND student_id = ?",
        (session_id, student_id)
    ).fetchone()
    if already:
        db.close()
        return jsonify({"error": "Attendance already marked for this student."}), 409

    # --- Location Validation ---
    if not is_plausible_location(lat, lon):
        db.close()
        return jsonify({"error": "Invalid GPS coordinates (possible spoofing)."}), 400

    loc_valid, distance = validate_location(
        lat, lon,
        session["lat"], session["lon"],
        session["radius"]
    )
    if not loc_valid:
        db.close()
        return jsonify({
            "error": f"You are {distance:.1f}m away — outside the {session['radius']}m classroom zone."
        }), 400

    # --- Anomaly Detection ---
    flags = []

    # 1. Duplicate device
    session_devices = [
        dict(r) for r in db.execute(
            "SELECT device_id, student_id FROM devices WHERE session_id = ?", (session_id,)
        ).fetchall()
    ]
    dup, prev_student = detect_duplicate_device(device_id, session_devices)
    if dup:
        flags.append("duplicate_device")

    # 2. Coordinate clustering
    all_coords = [
        (r["lat"], r["lon"]) for r in db.execute(
            "SELECT lat, lon FROM attendance WHERE session_id = ?", (session_id,)
        ).fetchall()
    ]
    all_coords.append((lat, lon))
    clustered, hotspot, cluster_count = detect_coordinate_clustering(all_coords)
    if clustered:
        flags.append("coordinate_cluster")

    risk = score_risk(flags)
    is_flagged = len(flags) > 0

    # --- Save to DB ---
    db.execute(
        """INSERT INTO attendance
           (session_id, student_id, student_name, device_id, lat, lon, distance, is_flagged, flag_reason)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (session_id, student_id, student_name, device_id,
         lat, lon, distance, is_flagged, ",".join(flags) if flags else None)
    )
    db.execute(
        "INSERT INTO devices (session_id, device_id, student_id) VALUES (?, ?, ?)",
        (session_id, device_id, student_id)
    )
    db.commit()
    db.close()

    return jsonify({
        "success": True,
        "message": "Attendance marked successfully! ✓",
        "student_name": student_name,
        "distance_m": distance,
        "flagged": is_flagged,
        "risk": risk if is_flagged else None
    }), 200


@attendance_bp.route("/list/<int:session_id>", methods=["GET"])
def list_attendance(session_id):
    """Fetch all attendance records for a session."""
    db = get_db()
    records = db.execute(
        """SELECT student_id, student_name, distance, is_flagged, flag_reason, marked_at
           FROM attendance WHERE session_id = ? ORDER BY marked_at DESC""",
        (session_id,)
    ).fetchall()
    db.close()

    return jsonify({
        "session_id": session_id,
        "count": len(records),
        "records": [dict(r) for r in records]
    })
