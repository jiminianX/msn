"""
Find the closest sports venue to a geographic coordinate.
"""

from geo.distance import distance_miles


def nearest_venue(latitude, longitude, venues):
    """
    Return the nearest venue and its distance in miles.

    Each venue must be a dictionary containing latitude
    and longitude. Returns None for an empty collection.
    """
    # Validate the search coordinates even for an empty list.
    distance_miles(latitude, longitude, latitude, longitude)

    if not venues:
        return None

    closest = None
    shortest_distance = float('inf')

    for venue in venues:
        if not isinstance(venue, dict):
            raise ValueError("Each venue must be a dictionary.")

        try:
            venue_lat = float(venue['latitude'])
            venue_lon = float(venue['longitude'])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("Venue has invalid coordinates.") from exc

        distance = distance_miles(
            latitude, longitude, venue_lat, venue_lon
        )

        if distance < shortest_distance:
            shortest_distance = distance
            closest = venue

    return {
        'venue': closest,
        'distance_miles': round(shortest_distance, 2),
    }
