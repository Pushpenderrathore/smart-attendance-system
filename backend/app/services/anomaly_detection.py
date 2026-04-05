from typing import List, Tuple, Optional

def detect_duplicate_device(device_id: str, session_devices: List[dict]) -> Tuple[bool, Optional[str]]:
    """
    Check if the same device is submitting attendance multiple times
    for different students in a single session.
    """
    for entry in session_devices:
        if entry["device_id"] == device_id:
            return True, entry.get("student_id", "unknown")
    return False, None


def detect_coordinate_clustering(
    locations: List[Tuple[float, float]],
    threshold: int = 5,
    precision: int = 4
) -> Tuple[bool, Optional[Tuple[float, float]], int]:
    """
    Detect if many students share suspiciously identical GPS coordinates —
    a strong signal they're sharing location data to fake attendance.

    Returns:
        (is_suspicious: bool, hotspot_coords: tuple|None, count: int)
    """
    freq: dict = {}
    for lat, lon in locations:
        key = (round(lat, precision), round(lon, precision))
        freq[key] = freq.get(key, 0) + 1

    for coords, count in freq.items():
        if count >= threshold:
            return True, coords, count

    return False, None, 0


def detect_impossible_speed(
    prev_lat: float, prev_lon: float, prev_time: float,
    curr_lat: float, curr_lon: float, curr_time: float,
    max_speed_mps: float = 30.0
) -> Tuple[bool, float]:
    """
    Flag if student "teleported" between locations (GPS spoofing via VPN/mock).
    max_speed_mps = 30 m/s (~108 km/h) — impossible on foot/bike.
    """
    from utils.haversine import haversine
    import math

    distance = haversine(prev_lat, prev_lon, curr_lat, curr_lon)
    time_diff = curr_time - prev_time

    if time_diff <= 0:
        return True, float("inf")

    speed = distance / time_diff
    return speed > max_speed_mps, round(speed, 2)


def score_risk(flags: List[str]) -> dict:
    """
    Compute a composite risk score from a list of flag strings.
    Returns score (0–100) and risk level.
    """
    weights = {
        "duplicate_device": 50,
        "coordinate_cluster": 40,
        "impossible_speed": 35,
        "null_island": 60,
        "otp_expired": 10,
    }

    score = 0
    for flag in flags:
        score += weights.get(flag, 10)

    score = min(score, 100)

    if score >= 70:
        level = "HIGH"
    elif score >= 35:
        level = "MEDIUM"
    else:
        level = "LOW"

    return {"score": score, "level": level, "flags": flags}
