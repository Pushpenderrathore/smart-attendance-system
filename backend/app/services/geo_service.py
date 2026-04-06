from utils.haversine import haversine

def validate_location(
    student_lat: float,
    student_lon: float,
    classroom_lat: float,
    classroom_lon: float,
    radius: int
) -> tuple[bool, float]:
    """
    Check whether student's GPS coordinates fall within the
    allowed geofence radius around the classroom.

    Returns:
        (is_within_bounds: bool, distance_meters: float)
    """
    if not (-90 <= student_lat <= 90 and -180 <= student_lon <= 180):
        return False, -1.0

    distance = haversine(student_lat, student_lon, classroom_lat, classroom_lon)
    return distance <= radius, round(distance, 2)


def is_plausible_location(lat: float, lon: float) -> bool:
    """
    Reject obviously spoofed or default coordinates
    (0,0 is the "null island" — common spoof default).
    """
    if lat == 0.0 and lon == 0.0:
        return False
    if lat is None or lon is None:
        return False
    return True
