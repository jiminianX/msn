"""
Tests for the nearest-venue calculation.
"""

import pytest

from geo.nearest import nearest_venue


@pytest.fixture
def sample_venues():
    return [
        {
            'name': 'Madison Square Garden',
            'latitude': 40.7505,
            'longitude': -73.9934,
        },
        {
            'name': 'Scotiabank Arena',
            'latitude': 43.6435,
            'longitude': -79.3791,
        },
        {
            'name': 'Crypto.com Arena',
            'latitude': 34.0430,
            'longitude': -118.2673,
        },
    ]


def test_finds_nearest_venue(sample_venues):
    result = nearest_venue(40.75, -73.99, sample_venues)

    assert result['venue']['name'] == 'Madison Square Garden'
    assert result['distance_miles'] < 1


def test_nearest_venue_from_los_angeles(sample_venues):
    result = nearest_venue(34.05, -118.25, sample_venues)

    assert result['venue']['name'] == 'Crypto.com Arena'


def test_empty_venue_list():
    assert nearest_venue(40.75, -73.99, []) is None


def test_invalid_search_coordinates(sample_venues):
    with pytest.raises(ValueError):
        nearest_venue(100, -73.99, sample_venues)


def test_missing_venue_coordinates():
    venues = [{'name': 'Unknown Arena', 'latitude': 40.75}]

    with pytest.raises(ValueError):
        nearest_venue(40.75, -73.99, venues)


def test_invalid_venue_coordinates():
    venues = [{
        'name': 'Invalid Arena',
        'latitude': 'not-a-number',
        'longitude': -73.99,
    }]

    with pytest.raises(ValueError):
        nearest_venue(40.75, -73.99, venues)
