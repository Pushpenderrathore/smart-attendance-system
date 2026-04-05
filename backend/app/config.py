import os

# Security
SECRET_KEY = os.getenv("SECRET_KEY", "smart-attend-secret-2024")

# OTP Settings
OTP_EXPIRY_SECONDS = int(os.getenv("OTP_EXPIRY_SECONDS", 60))
OTP_LENGTH = 6

# Geofencing
GEOFENCE_RADIUS = int(os.getenv("GEOFENCE_RADIUS", 100))   # meters
CLASSROOM_LAT = float(os.getenv("CLASSROOM_LAT", 28.7041))
CLASSROOM_LON = float(os.getenv("CLASSROOM_LON", 77.1025))

# Anomaly Detection
DUPLICATE_COORD_THRESHOLD = 5   # Flag if 5+ students share exact GPS coords
COORD_PRECISION = 4             # Decimal places to round for clustering check

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///attendance.db")
