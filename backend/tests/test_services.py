"""
Unit Tests v2 — Smart Attendance System
Run: python -m pytest tests/ -v
"""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))


# ══ OTP SERVICE (Secure) ═══════════════════════════════════
from services.otp_service import (
    generate_otp, verify_otp, refresh_otp,
    invalidate_otp, get_otp_age, get_attempt_info
)

def test_otp_generate_format():
    otp = generate_otp(100)
    assert len(otp) == 6 and otp.isdigit()

def test_otp_verify_correct():
    otp = generate_otp(101)
    valid, msg = verify_otp(101, otp)
    assert valid is True

def test_otp_verify_wrong():
    generate_otp(102)
    valid, msg = verify_otp(102, "000000")
    assert valid is False
    assert "attempt" in msg.lower()

def test_otp_brute_force_lockout():
    """After 3 wrong attempts, account should lock."""
    generate_otp(103)
    for _ in range(3):
        verify_otp(103, "000000")
    valid, msg = verify_otp(103, "000000")
    assert valid is False
    assert "locked" in msg.lower() or "too many" in msg.lower()

def test_otp_attempt_counter():
    generate_otp(104)
    verify_otp(104, "000000")
    info = get_attempt_info(104)
    assert info["attempts"] == 1
    assert info["locked"] is False

def test_otp_expired():
    otp = generate_otp(105)
    valid, msg = verify_otp(105, otp, expiry=0)
    assert valid is False and "expired" in msg.lower()

def test_otp_missing_session():
    valid, _ = verify_otp(99999, "123456")
    assert valid is False

def test_otp_refresh_clears_lockout():
    generate_otp(106)
    for _ in range(3):
        verify_otp(106, "000000")
    new_otp = refresh_otp(106)    # teacher refreshes
    valid, _ = verify_otp(106, new_otp)
    assert valid is True           # lockout cleared

def test_otp_invalidate():
    generate_otp(107)
    invalidate_otp(107)
    valid, _ = verify_otp(107, "123456")
    assert valid is False

def test_otp_correct_after_one_fail():
    """One wrong guess should not block a correct one."""
    otp = generate_otp(108)
    verify_otp(108, "000000")
    valid, _ = verify_otp(108, otp)
    assert valid is True

# ══ HAVERSINE ══════════════════════════════════════════════
from utils.haversine import haversine

def test_haversine_zero():
    assert haversine(28.7041, 77.1025, 28.7041, 77.1025) == 0.0

def test_haversine_delhi_mumbai():
    d = haversine(28.6139, 77.2090, 19.0760, 72.8777)
    assert 1_100_000 < d < 1_200_000

def test_haversine_small():
    d = haversine(28.7041, 77.1025, 28.7042, 77.1025)
    assert d < 200

# ══ GEO SERVICE (Upgraded) ═════════════════════════════════
from services.geo_service import (
    validate_location, is_plausible_location,
    check_gps_accuracy, validate_location_samples, comprehensive_location_check
)

def test_inside_geofence():
    valid, d = validate_location(28.7041, 77.1025, 28.7041, 77.1025, 100)
    assert valid is True and d == 0.0

def test_outside_geofence():
    valid, d = validate_location(28.7041, 77.1025, 28.7200, 77.1025, 100)
    assert valid is False and d > 100

def test_null_island():
    assert is_plausible_location(0.0, 0.0) is False

def test_plausible_real_coords():
    assert is_plausible_location(28.7041, 77.1025) is True

def test_gps_accuracy_good():
    ok, flag = check_gps_accuracy(10.0)
    assert ok is True and flag is None

def test_gps_accuracy_low():
    ok, flag = check_gps_accuracy(100.0, threshold=50.0)
    assert ok is False and "low_accuracy" in flag

def test_gps_samples_consistent():
    samples = [
        {"lat": 28.7041, "lon": 77.1025},
        {"lat": 28.70412, "lon": 77.10252},
        {"lat": 28.70409, "lon": 77.10248},
    ]
    ok, spread, flag = validate_location_samples(samples)
    assert ok is True and flag is None

def test_gps_samples_static_suspicious():
    """Identical readings = likely mock GPS."""
    samples = [{"lat":28.7041,"lon":77.1025}] * 3
    ok, spread, flag = validate_location_samples(samples)
    assert ok is False and "static" in flag

def test_comprehensive_check_inside():
    result = comprehensive_location_check(28.7041, 77.1025, 10.0, [], 28.7041, 77.1025, 100)
    assert result["valid"] is True

def test_comprehensive_check_outside():
    result = comprehensive_location_check(28.7200, 77.1025, 10.0, [], 28.7041, 77.1025, 100)
    assert result["valid"] is False

def test_comprehensive_null_island():
    result = comprehensive_location_check(0.0, 0.0, 10.0, [], 28.7041, 77.1025, 100)
    assert result["valid"] is False and "null_island" in result["flags"]

# ══ ANOMALY DETECTION ══════════════════════════════════════
from services.anomaly_detection import (
    detect_duplicate_device, detect_coordinate_clustering, score_risk
)

def test_duplicate_device():
    devices = [{"device_id": "dev_abc", "student_id": "S001"}]
    found, prev = detect_duplicate_device("dev_abc", devices)
    assert found and prev == "S001"

def test_no_duplicate():
    devices = [{"device_id": "dev_abc", "student_id": "S001"}]
    found, _ = detect_duplicate_device("dev_xyz", devices)
    assert not found

def test_cluster_triggered():
    locs = [(28.7041, 77.1025)] * 6
    flagged, _, count = detect_coordinate_clustering(locs, threshold=5)
    assert flagged and count >= 5

def test_no_cluster():
    locs = [(28.7041 + i*0.01, 77.1025) for i in range(4)]
    flagged, _, _ = detect_coordinate_clustering(locs, threshold=5)
    assert not flagged

def test_risk_high():
    r = score_risk(["duplicate_device", "coordinate_cluster"])
    assert r["level"] == "HIGH" and r["score"] >= 70

def test_risk_low():
    r = score_risk([])
    assert r["level"] == "LOW" and r["score"] == 0

# ══ JWT AUTH ═══════════════════════════════════════════════
from auth.jwt_service import generate_token, verify_token, login, logout

def test_token_generated():
    t = generate_token("user1", "teacher")
    assert t and len(t.split(".")) == 3

def test_token_verify_valid():
    t = generate_token("user2", "teacher")
    payload, err = verify_token(t)
    assert err is None and payload["sub"] == "user2"

def test_token_verify_invalid():
    _, err = verify_token("bad.token.here")
    assert err is not None

def test_token_verify_empty():
    _, err = verify_token("")
    assert err is not None

def test_login_success():
    token, user = login("teacher_001", "teacher123")
    assert token is not None and user["role"] == "teacher"

def test_login_wrong_password():
    token, err = login("teacher_001", "wrongpassword")
    assert token is None and "incorrect" in err.lower()

def test_login_unknown_user():
    token, err = login("ghost_user", "abc123")
    assert token is None

def test_logout_blacklists_token():
    token, _ = login("teacher_001", "teacher123")
    logout(token)
    _, err = verify_token(token)
    assert "revoked" in err.lower()

# ══ RATE LIMITER ═══════════════════════════════════════════
from middleware.rate_limiter import _request_log, rate_limit
from collections import deque
import time as _time

def test_rate_limiter_allows_under_limit():
    key = "test_fn:127.0.0.1"
    _request_log[key] = deque()
    now = _time.time()
    for _ in range(4):
        _request_log[key].append(now)
    assert len(_request_log[key]) < 5

def test_rate_limiter_expires_old():
    key = "old_fn:127.0.0.1"
    old_time = _time.time() - 120  # 2 minutes ago
    _request_log[key] = deque([old_time, old_time])
    window = 60
    now = _time.time()
    while _request_log[key] and _request_log[key][0] < now - window:
        _request_log[key].popleft()
    assert len(_request_log[key]) == 0   # all evicted
