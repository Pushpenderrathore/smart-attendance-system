from flask import Blueprint, jsonify, request
from database import get_db

teacher_bp = Blueprint("teacher", __name__)

@teacher_bp.route("/sessions/<teacher_id>", methods=["GET"])
def get_sessions(teacher_id):
    """Get all sessions created by a teacher."""
    db = get_db()
    sessions = db.execute(
        """SELECT s.id, s.subject, s.is_active, s.created_at,
                  COUNT(a.id) as total_attendance,
                  SUM(a.is_flagged) as flagged_count
           FROM sessions s
           LEFT JOIN attendance a ON a.session_id = s.id
           WHERE s.teacher_id = ?
           GROUP BY s.id
           ORDER BY s.created_at DESC""",
        (teacher_id,)
    ).fetchall()
    db.close()

    return jsonify({
        "teacher_id": teacher_id,
        "sessions": [dict(s) for s in sessions]
    })


@teacher_bp.route("/report/<int:session_id>", methods=["GET"])
def session_report(session_id):
    """Full report for a session including flagged records."""
    db = get_db()

    session = db.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
    if not session:
        db.close()
        return jsonify({"error": "Session not found"}), 404

    records = db.execute(
        """SELECT * FROM attendance WHERE session_id = ? ORDER BY marked_at""",
        (session_id,)
    ).fetchall()

    stats = db.execute(
        """SELECT COUNT(*) as total,
                  SUM(is_flagged) as flagged,
                  AVG(distance) as avg_distance,
                  MIN(distance) as min_distance,
                  MAX(distance) as max_distance
           FROM attendance WHERE session_id = ?""",
        (session_id,)
    ).fetchone()

    db.close()

    return jsonify({
        "session": dict(session),
        "statistics": dict(stats),
        "attendance": [dict(r) for r in records]
    })


@teacher_bp.route("/flagged/<int:session_id>", methods=["GET"])
def flagged_records(session_id):
    """Return only suspicious attendance records."""
    db = get_db()
    records = db.execute(
        """SELECT student_id, student_name, lat, lon, distance, flag_reason, marked_at
           FROM attendance WHERE session_id = ? AND is_flagged = 1""",
        (session_id,)
    ).fetchall()
    db.close()

    return jsonify({
        "session_id": session_id,
        "flagged_count": len(records),
        "records": [dict(r) for r in records]
    })
