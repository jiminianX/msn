import pytest

import data.load as ld


def test_load_countries():
    countries = ld.load_countries()
    assert 'US' in countries
    assert 'CA' in countries
    assert countries['CA']['name'] == 'Canada'


def test_load_leagues():
    leagues = ld.load_leagues()
    assert 'NBA' in leagues
    assert 'MLS' in leagues
    assert leagues['MLS']['sport'] == 'Soccer'


def test_load_csv_missing_file():
    with pytest.raises(FileNotFoundError):
        ld.load_csv('no/such/file.csv')


def test_get_country():
    country = ld.get_country('us')
    assert country['name'] == 'United States'
    assert ld.get_country('US') == country


def test_get_country_not_found():
    assert ld.get_country('ZZ') is None
    assert ld.get_country(None) is None


def test_get_league():
    league = ld.get_league('nba')
    assert league['sport'] == 'Basketball'
    assert ld.get_league('NBA') == league


def test_get_league_not_found():
    assert ld.get_league('XFL') is None
    assert ld.get_league(None) is None


VENUE_FIELDS = (
    'venue_id', 'name', 'city', 'state_code', 'country_code',
    'capacity', 'opened_year', 'latitude', 'longitude', 'indoor',
)


def test_load_venues():
    venues = ld.load_venues()
    assert isinstance(venues, dict)
    assert len(venues) > 10
    assert 'MSG' in venues
    assert venues['MSG']['name'] == 'Madison Square Garden'


def test_load_venues_has_every_documented_field():
    for venue_id, venue in ld.load_venues().items():
        for field in VENUE_FIELDS:
            assert field in venue, f'{venue_id} is missing {field}'
            assert venue[field] != '', f'{venue_id} has an empty {field}'


def test_load_venues_coordinates_are_usable():
    # The geo utilities float() these, so a bad row would only
    # surface as a ValueError deep inside a distance calculation.
    for venue_id, venue in ld.load_venues().items():
        latitude = float(venue['latitude'])
        longitude = float(venue['longitude'])
        assert -90 <= latitude <= 90, venue_id
        assert -180 <= longitude <= 180, venue_id


def test_load_venues_covers_both_countries():
    countries = {v['country_code'] for v in ld.load_venues().values()}
    assert countries == {'US', 'CA'}


def test_get_venue():
    venue = ld.get_venue('msg')
    assert venue['city'] == 'New York'
    assert venue['state_code'] == 'NY'
    assert ld.get_venue('MSG') == venue


def test_get_venue_not_found():
    assert ld.get_venue('NOPE') is None
    assert ld.get_venue(None) is None
