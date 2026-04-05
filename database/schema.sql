-- ============================================================
--  Smart Attendance System — Database Schema
--  Compatible: MySQL 8.0+ / PostgreSQL 14+ / SQLite 3.35+
-- ============================================================

-- ─── TEACHERS ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS teachers (
    id          VARCHAR(50)  PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    email       VARCHAR(150) UNIQUE NOT NULL,
    department  VARCHAR(100),
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ─── SESSIONS ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS sessions (
    id          INTEGER      PRIMARY KEY AUTOINCREMENT,
    teacher_id  VARCHAR(50)  NOT NULL REFERENCES teachers(id),
    subject     VARCHAR(100) NOT NULL,
    otp         VARCHAR(6)   NOT NULL,
    lat         REAL         NOT NULL,   -- Classroom latitude
    lon         REAL         NOT NULL,   -- Classroom longitude
    radius      INTEGER      NOT NULL DEFAULT 100,  -- Geofence in meters
    created_at  TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    expires_at  TIMESTAMP,
    is_active   BOOLEAN      DEFAULT 1
);

-- ─── ATTENDANCE ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS attendance (
    id           INTEGER     PRIMARY KEY AUTOINCREMENT,
    session_id   INTEGER     NOT NULL REFERENCES sessions(id),
    student_id   VARCHAR(50) NOT NULL,
    student_name VARCHAR(100) NOT NULL,
    device_id    VARCHAR(200) NOT NULL,  -- Browser fingerprint / device UUID
    lat          REAL        NOT NULL,
    lon          REAL        NOT NULL,
    distance     REAL        NOT NULL,   -- Distance from classroom in meters
    is_flagged   BOOLEAN     DEFAULT 0,
    flag_reason  TEXT,                   -- Comma-separated flag codes
    marked_at    TIMESTAMP   DEFAULT CURRENT_TIMESTAMP
);

-- ─── DEVICE REGISTRY ──────────────────────────────────────
CREATE TABLE IF NOT EXISTS devices (
    id            INTEGER     PRIMARY KEY AUTOINCREMENT,
    session_id    INTEGER     NOT NULL REFERENCES sessions(id),
    device_id     VARCHAR(200) NOT NULL,
    student_id    VARCHAR(50) NOT NULL,
    registered_at TIMESTAMP   DEFAULT CURRENT_TIMESTAMP
);

-- ─── INDEXES ──────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_attendance_session ON attendance(session_id);
CREATE INDEX IF NOT EXISTS idx_attendance_student ON attendance(student_id);
CREATE INDEX IF NOT EXISTS idx_devices_session    ON devices(session_id);
CREATE INDEX IF NOT EXISTS idx_sessions_teacher   ON sessions(teacher_id);
