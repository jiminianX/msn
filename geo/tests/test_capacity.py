"""
Tests for venue capacity rankings.
"""

import pytest

from geo.capacity import rank_venues_by_capacity


@pytest.fixture
def sample_venues():
    return [
        {
            'name': 'Arena A',
            'state_code': 'NY',
            'capacity': '19000',
        },
        {
            'name': 'Stadium B',
            'state_code': 'CA',
            'capacity': '25000',
        },
        {
            'name': 'Arena C',
            'state_code': 'NY',
            'capacity': '21000',
        },
    ]


def test_rank_by_capacity(sample_venues):
    result = rank_venues_by_capacity(sample_venues)

    assert [v['name'] for v in result] == [
        'Stadium B', 'Arena C', 'Arena A'
    ]


def test_filter_by_state(sample_venues):
    result = rank_venues_by_capacity(sample_venues, 'NY')

    assert [v['name'] for v in result] == [
        'Arena C', 'Arena A'
    ]


def test_case_insensitive_state_filter(sample_venues):
    result = rank_venues_by_capacity(sample_venues, 'ny')
    assert len(result) == 2


def test_empty_venues():
    assert rank_venues_by_capacity([]) == []


def test_no_matching_state(sample_venues):
    assert rank_venues_by_capacity(sample_venues, 'FL') == []


def test_invalid_capacity():
    venues = [{'name': 'Bad Arena', 'capacity': 'unknown'}]

    with pytest.raises(ValueError):
        rank_venues_by_capacity(venues)


def test_negative_capacity():
    venues = [{'name': 'Bad Arena', 'capacity': -100}]

    with pytest.raises(ValueError):
        rank_venues_by_capacity(venues)


def test_original_data_unchanged(sample_venues):
    original_order = [v['name'] for v in sample_venues]

    rank_venues_by_capacity(sample_venues)

    assert [v['name'] for v in sample_venues] == original_order


def test_filter_by_country():
    venues = [
        {'name': 'US Arena', 'country_code': 'US',
         'capacity': 20000},
        {'name': 'Canada Arena', 'country_code': 'CA',
         'capacity': 19000},
    ]

    result = rank_venues_by_capacity(venues, country_code='CA')

    assert [v['name'] for v in result] == ['Canada Arena']


def test_country_filter_case_insensitive():
    venues = [
        {'name': 'Canada Arena', 'country_code': 'CA',
         'capacity': 19000},
    ]

    result = rank_venues_by_capacity(venues, country_code='ca')

    assert len(result) == 1


def test_invalid_country_filter():
    with pytest.raises(ValueError):
        rank_venues_by_capacity([], country_code=123)
