"""
Unit tests for Smart Attendance System
Run: python -m pytest tests/ -v
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

import time
import pytest

# ── OTP SERVICE TESTS ────────────────────────────────────────
from services.otp_service import generate_otp, verify_otp, refresh_otp, invalidate_otp, get_otp_age

def test_otp_generation():
    otp = generate_otp(999)
    assert len(otp) == 6
    assert otp.isdigit()

def test_otp_valid():
    otp = generate_otp(1)
    valid, msg = verify_otp(1, otp)
    assert valid is True
    assert "verified" in msg.lower()

def test_otp_wrong():
    generate_otp(2)
    valid, msg = verify_otp(2, "000000")
    assert valid is False
    assert "invalid" in msg.lower()

def test_otp_expired():
    otp = generate_otp(3)
    valid, msg = verify_otp(3, otp, expiry=0)
    assert valid is False
    assert "expired" in msg.lower()

def test_otp_missing_session():
    valid, msg = verify_otp(9999, "123456")
    assert valid is False

def test_otp_refresh():
    otp1 = generate_otp(4)
    otp2 = refresh_otp(4)
    # Refreshed OTP should still verify correctly
    valid, _ = verify_otp(4, otp2)
    assert valid is True

def test_otp_invalidate():
    generate_otp(5)
    invalidate_otp(5)
    valid, _ = verify_otp(5, "123456")
    assert valid is False

def test_otp_age():
    generate_otp(6)
    time.sleep(0.05)
    age = get_otp_age(6)
    assert age is not None
    assert age >= 0.05

# ── HAVERSINE TESTS ──────────────────────────────────────────
from utils.haversine import haversine

def test_haversine_same_point():
    dist = haversine(28.7041, 77.1025, 28.7041, 77.1025)
    assert dist == 0.0

def test_haversine_known_distance():
    # Delhi to Mumbai ~ 1150 km
    dist = haversine(28.6139, 77.2090, 19.0760, 72.8777)
    assert 1_100_000 < dist < 1_200_000

def test_haversine_small_distance():
    # ~111 meters per 0.001 degrees latitude
    dist = haversine(28.7041, 77.1025, 28.7042, 77.1025)
    assert dist < 200

# ── GEO SERVICE TESTS ────────────────────────────────────────
from services.geo_service import validate_location, is_plausible_location

def test_inside_geofence():
    valid, dist = validate_location(28.7041, 77.1025, 28.7041, 77.1025, radius=100)
    assert valid is True
    assert dist == 0.0

def test_outside_geofence():
    # ~1.1km away
    valid, dist = validate_location(28.7041, 77.1025, 28.7140, 77.1025, radius=100)
    assert valid is False
    assert dist > 100

def test_plausible_location():
    assert is_plausible_location(28.7041, 77.1025) is True
    assert is_plausible_location(0.0, 0.0) is False
    assert is_plausible_location(None, None) is False

# ── ANOMALY DETECTION TESTS ──────────────────────────────────
from services.anomaly_detection import (
    detect_duplicate_device,
    detect_coordinate_clustering,
    score_risk
)

def test_duplicate_device_found():
    devices = [{"device_id": "dev_abc", "student_id": "S001"}]
    found, prev = detect_duplicate_device("dev_abc", devices)
    assert found is True
    assert prev == "S001"

def test_duplicate_device_not_found():
    devices = [{"device_id": "dev_abc", "student_id": "S001"}]
    found, _ = detect_duplicate_device("dev_xyz", devices)
    assert found is False

def test_coordinate_clustering_triggered():
    locs = [(28.7041, 77.1025)] * 6
    flagged, hotspot, count = detect_coordinate_clustering(locs, threshold=5)
    assert flagged is True
    assert count >= 5

def test_coordinate_clustering_ok():
    locs = [(28.7041 + i * 0.01, 77.1025 + i * 0.01) for i in range(10)]
    flagged, _, _ = detect_coordinate_clustering(locs, threshold=5)
    assert flagged is False

def test_risk_score_high():
    result = score_risk(["duplicate_device", "coordinate_cluster"])
    assert result["level"] == "HIGH"
    assert result["score"] >= 70

def test_risk_score_low():
    result = score_risk([])
    assert result["level"] == "LOW"
    assert result["score"] == 0
