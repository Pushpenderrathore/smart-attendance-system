import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "attendance.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.executescript("""
        -- Teachers table (was missing password_hash + role in original)
        CREATE TABLE IF NOT EXISTS teachers (
            id              TEXT PRIMARY KEY,
            name            TEXT NOT NULL,
            email           TEXT UNIQUE,
            department      TEXT,
            password_hash   TEXT NOT NULL DEFAULT '',
            role            TEXT NOT NULL DEFAULT 'teacher',
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS sessions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id  TEXT NOT NULL,
            subject     TEXT NOT NULL,
            otp         TEXT NOT NULL,
            lat         REAL NOT NULL,
            lon         REAL NOT NULL,
            radius      INTEGER NOT NULL DEFAULT 100,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at  TIMESTAMP,
            is_active   BOOLEAN DEFAULT 1,
            FOREIGN KEY (teacher_id) REFERENCES teachers(id)
        );

        CREATE TABLE IF NOT EXISTS attendance (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id  INTEGER NOT NULL,
            student_id  TEXT NOT NULL,
            student_name TEXT NOT NULL,
            device_id   TEXT NOT NULL,
            lat         REAL NOT NULL,
            lon         REAL NOT NULL,
            distance    REAL NOT NULL,
            is_flagged  BOOLEAN DEFAULT 0,
            flag_reason TEXT,
            marked_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        );

        CREATE TABLE IF NOT EXISTS devices (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id  INTEGER NOT NULL,
            device_id   TEXT NOT NULL,
            student_id  TEXT NOT NULL,
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.commit()
    conn.close()
    print("[DB] Database initialized.")

    # Seed default teachers if the table is empty
    _seed_if_empty()


def _seed_if_empty():
    """
    On a brand-new DB, seed the two default teachers so the system
    works out of the box without a manual step.
    Skips if teachers already exist.
    """
    conn = get_db()
    count = conn.execute("SELECT COUNT(*) FROM teachers").fetchone()[0]
    conn.close()

    if count == 0:
        # Import here to avoid circular import at module load
        from auth.jwt_service import seed_default_teachers
        seed_default_teachers()


init_db()