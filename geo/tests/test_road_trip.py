"""
Tests for the multi-venue road-trip calculator.
"""

import pytest

from geo.distance import distance_miles
from geo.road_trip import road_trip_miles


@pytest.fixture
def sample_venues():
    return [
        {'name': 'A', 'latitude': 40.0, 'longitude': -74.0},
        {'name': 'B', 'latitude': 41.0, 'longitude': -73.0},
        {'name': 'C', 'latitude': 42.0, 'longitude': -72.0},
    ]


def test_empty_road_trip():
    assert road_trip_miles([]) == 0


def test_single_venue():
    venue = {'latitude': 40.0, 'longitude': -74.0}
    assert road_trip_miles([venue]) == 0


def test_two_venue_trip(sample_venues):
    expected = distance_miles(40, -74, 41, -73)
    assert road_trip_miles(sample_venues[:2]) == pytest.approx(
        expected, abs=0.01
    )


def test_three_venue_trip(sample_venues):
    first_leg = distance_miles(40, -74, 41, -73)
    second_leg = distance_miles(41, -73, 42, -72)

    assert road_trip_miles(sample_venues) == pytest.approx(
        first_leg + second_leg, abs=0.01
    )


def test_trip_order_changes_distance(sample_venues):
    original = road_trip_miles(sample_venues)
    reordered = road_trip_miles([
        sample_venues[0], sample_venues[2], sample_venues[1]
    ])

    assert original != reordered


def test_invalid_venue():
    with pytest.raises(ValueError):
        road_trip_miles([{'latitude': 40.0}])


def test_out_of_range_coordinates():
    with pytest.raises(ValueError):
        road_trip_miles([
            {'latitude': 95.0, 'longitude': -74.0}
        ])
