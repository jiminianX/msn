"""
Calculate the total great-circle distance of a multi-venue trip.
"""

from geo.distance import distance_miles


def road_trip_miles(venues):
    """
    Return the total distance between consecutive venues in miles.

    Venues must be ordered dictionaries with latitude and longitude.
    An empty or single-venue trip has zero travel distance.
    """
    coordinates = []

    for venue in venues:
        if not isinstance(venue, dict):
            raise ValueError("Each venue must be a dictionary.")

        try:
            lat = float(venue['latitude'])
            lon = float(venue['longitude'])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("Venue has invalid coordinates.") from exc

        # Reuse the existing validation in distance_miles().
        distance_miles(lat, lon, lat, lon)
        coordinates.append((lat, lon))

    total = 0.0

    for index in range(1, len(coordinates)):
        lat1, lon1 = coordinates[index - 1]
        lat2, lon2 = coordinates[index]
        total += distance_miles(lat1, lon1, lat2, lon2)

    return round(total, 2)
