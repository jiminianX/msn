"""
Geographic distance calculations for sports venues.
"""

import math

EARTH_RADIUS_MILES = 3958.8


def distance_miles(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance between two coordinates.

    Coordinates are given in decimal degrees.
    Returns the distance in miles.
    """
    coordinates = (lat1, lon1, lat2, lon2)

    for value in coordinates:
        if not isinstance(value, (int, float)):
            raise ValueError("Coordinates must be numeric.")

        if not math.isfinite(value):
            raise ValueError("Coordinates must be finite.")

    if not (-90 <= lat1 <= 90 and -90 <= lat2 <= 90):
        raise ValueError("Latitude must be between -90 and 90.")

    if not (-180 <= lon1 <= 180 and -180 <= lon2 <= 180):
        raise ValueError("Longitude must be between -180 and 180.")

    # Convert degrees to radians.
    lat1, lon1, lat2, lon2 = map(math.radians, coordinates)

    # Calculate differences between coordinates.
    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1

    # Haversine formula.
    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2)
        * math.sin(delta_lon / 2) ** 2
    )

    # Keep a within the valid range for floating-point safety.
    a = min(1.0, max(0.0, a))

    central_angle = 2 * math.asin(math.sqrt(a))

    return EARTH_RADIUS_MILES * central_angle
