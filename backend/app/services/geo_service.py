"""
Geo Validation Service (upgraded)
──────────────────────────────────
✅ Geofence check (haversine)
✅ GPS accuracy threshold (flag if > 50m accuracy)
✅ Null-island / obviously spoofed coord detection
✅ Multi-sample consistency check (3 readings must agree within 30m)
"""
from utils.haversine import haversine


def validate_location(student_lat, student_lon, classroom_lat, classroom_lon, radius) -> tuple:
    """
    Check student is within geofence.
    Returns (is_valid: bool, distance_m: float)
    """
    if not is_plausible_location(student_lat, student_lon):
        return False, -1.0
    distance = haversine(student_lat, student_lon, classroom_lat, classroom_lon)
    return distance <= radius, round(distance, 2)


def is_plausible_location(lat, lon) -> bool:
    """Reject null-island and None values."""
    if lat is None or lon is None:
        return False
    if lat == 0.0 and lon == 0.0:
        return False
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return False
    return True


def check_gps_accuracy(accuracy_meters: float, threshold: float = 50.0) -> tuple:
    """
    Flag low-accuracy GPS readings — often a sign of VPN/mock GPS.
    Returns (is_accurate: bool, flag: str|None)
    """
    if accuracy_meters is None:
        return True, None   # accuracy not reported — allow but note
    if accuracy_meters > threshold:
        return False, f"low_accuracy:{accuracy_meters:.0f}m"
    return True, None


def validate_location_samples(samples: list, max_spread_m: float = 30.0) -> tuple:
    """
    Validate 2–3 GPS samples collected a few seconds apart.
    If they're spread > max_spread_m apart, flag as possibly spoofed
    (real GPS jitter is <10m; mock GPS sends identical coords).

    Args:
        samples: list of {"lat": float, "lon": float}
        max_spread_m: max allowed spread between any two samples

    Returns:
        (is_consistent: bool, spread_m: float, flag: str|None)
    """
    if len(samples) < 2:
        return True, 0.0, None

    max_dist = 0.0
    for i in range(len(samples)):
        for j in range(i + 1, len(samples)):
            d = haversine(
                samples[i]["lat"], samples[i]["lon"],
                samples[j]["lat"], samples[j]["lon"]
            )
            max_dist = max(max_dist, d)

    # Identical samples (spread = 0) are MORE suspicious than slight jitter
    if max_dist == 0.0 and len(samples) >= 2:
        return False, 0.0, "gps_static_suspicious"

    if max_dist > max_spread_m:
        return False, round(max_dist, 2), f"gps_spread:{max_dist:.0f}m"

    return True, round(max_dist, 2), None


def comprehensive_location_check(
    lat, lon, accuracy,
    samples,
    classroom_lat, classroom_lon, radius
) -> dict:
    """
    Run all GPS checks and return a unified result.
    """
    flags  = []
    result = {"valid": True, "distance_m": None, "flags": flags}

    # 1. Plausibility
    if not is_plausible_location(lat, lon):
        result["valid"] = False
        flags.append("null_island")
        return result

    # 2. Geofence
    inside, distance = validate_location(lat, lon, classroom_lat, classroom_lon, radius)
    result["distance_m"] = distance
    if not inside:
        result["valid"] = False
        flags.append(f"outside_geofence:{distance:.0f}m")

    # 3. Accuracy
    accurate, acc_flag = check_gps_accuracy(accuracy)
    if not accurate:
        flags.append(acc_flag)   # flag but don't block (teacher can override)

    # 4. Multi-sample consistency
    if samples:
        consistent, spread, spread_flag = validate_location_samples(samples)
        if not consistent:
            flags.append(spread_flag)

    return result
