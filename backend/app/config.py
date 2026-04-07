import os

# ── Security ───────────────────────────────────────────────
SECRET_KEY = os.getenv("SECRET_KEY", "CHANGE-THIS-IN-PRODUCTION-USE-RANDOM-64-CHARS")

# ── OTP ────────────────────────────────────────────────────
OTP_EXPIRY_SECONDS = int(os.getenv("OTP_EXPIRY_SECONDS", 60))
OTP_LENGTH         = 6
OTP_MAX_ATTEMPTS   = 3
OTP_LOCK_SECONDS   = 60

# ── Geofencing ─────────────────────────────────────────────
GEOFENCE_RADIUS    = int(os.getenv("GEOFENCE_RADIUS", 100))    # meters
CLASSROOM_LAT      = float(os.getenv("CLASSROOM_LAT", 28.7041))
CLASSROOM_LON      = float(os.getenv("CLASSROOM_LON", 77.1025))

# ── GPS Validation ─────────────────────────────────────────
GPS_ACCURACY_THRESHOLD = 50.0   # flag if accuracy > 50m
GPS_SAMPLE_COUNT       = 3      # collect 3 readings
GPS_SAMPLE_INTERVAL_MS = 2000   # 2s between each
GPS_MAX_SPREAD_M       = 30.0   # max allowed spread between samples

# ── Anomaly Detection ──────────────────────────────────────
DUPLICATE_COORD_THRESHOLD = 5
COORD_PRECISION           = 4

# ── Rate Limiting ──────────────────────────────────────────
RATE_ATTENDANCE_MAX  = 3
RATE_ATTENDANCE_WIN  = 60
RATE_LOGIN_MAX       = 5
RATE_LOGIN_WIN       = 60

# ── Database ───────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///attendance.db")

# ── JWT ────────────────────────────────────────────────────
TOKEN_EXPIRY_SECONDS = 3600   # 1 hour
