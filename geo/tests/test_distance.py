"""
Unit tests for geographic distance calculations.
"""

import pytest

from geo.distance import distance_miles


def test_same_coordinates():
    """The distance from a location to itself should be zero."""
    assert distance_miles(40.7128, -74.0060,
                          40.7128, -74.0060) == pytest.approx(0)


def test_new_york_to_los_angeles():
    """Check the approximate distance between NYC and LA."""
    distance = distance_miles(
        40.7128, -74.0060,
        34.0522, -118.2437,
    )

    assert distance == pytest.approx(2445, abs=10)


def test_distance_is_symmetric():
    """Travel direction should not affect great-circle distance."""
    forward = distance_miles(
        40.7128, -74.0060,
        34.0522, -118.2437,
    )

    backward = distance_miles(
        34.0522, -118.2437,
        40.7128, -74.0060,
    )

    assert forward == pytest.approx(backward)


@pytest.mark.parametrize(
    "coordinates",
    [
        (91, 0, 40, 0),
        (-91, 0, 40, 0),
        (40, 181, 20, 0),
        (40, -181, 20, 0),
        (float("nan"), 0, 20, 0),
        (float("inf"), 0, 20, 0),
        ("invalid", 0, 20, 0),
        (True, 0, 20, 0),
        (0, False, 20, 0),
    ],
)
def test_invalid_coordinates(coordinates):
    """Invalid coordinates should raise ValueError."""
    with pytest.raises(ValueError):
        distance_miles(*coordinates)
