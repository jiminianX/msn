"""
Rank sports venues by seating capacity.
"""


def rank_venues_by_capacity(venues, state_code=None, country_code=None):
    """
    Return venues sorted by capacity, highest first.

    Optionally filter by a two-letter state/province code.
    The original venue dictionaries are not modified.
    Optionally filter venues by country code.
    """
    if state_code is not None and not isinstance(state_code, str):
        raise ValueError("State code must be a string.")

    if country_code is not None and not isinstance(country_code, str):
        raise ValueError("Country code must be a string.")

    ranked = []

    for venue in venues:
        if not isinstance(venue, dict):
            raise ValueError("Each venue must be a dictionary.")

        if state_code is not None:
            venue_state = venue.get('state_code', '')
            if not isinstance(venue_state, str):
                raise ValueError("Invalid state code.")

            if venue_state.upper() != state_code.upper():
                continue

        if country_code is not None:
            venue_country = venue.get('country_code', '')
            if not isinstance(venue_country, str):
                raise ValueError("Invalid country code.")

            if venue_country.upper() != country_code.upper():
                continue

        capacity = venue.get('capacity')

        if isinstance(capacity, bool):
            raise ValueError("Invalid venue capacity.")

        try:
            numeric_capacity = int(capacity)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError("Invalid venue capacity.") from exc

        if isinstance(capacity, float) and not capacity.is_integer():
            raise ValueError("Capacity must be a whole number.")

        if numeric_capacity < 0:
            raise ValueError("Capacity cannot be negative.")

        ranked.append((numeric_capacity, venue))

    ranked.sort(key=lambda item: item[0], reverse=True)

    return [venue for _, venue in ranked]
