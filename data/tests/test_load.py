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


VENUE_FIELD_TYPES = {
    'venue_id': str,
    'name': str,
    'city': str,
    'state_code': str,
    'country_code': str,
    'capacity': int,
    'opened_year': int,
    'latitude': float,
    'longitude': float,
    'indoor': bool,
}


def test_load_venues_field_types():
    for venue_id, venue in ld.load_venues().items():
        for field, expected in VENUE_FIELD_TYPES.items():
            assert isinstance(venue[field], expected), (
                f'{venue_id}.{field} is {type(venue[field]).__name__}, '
                f'expected {expected.__name__}')


def test_load_venues_indoor_distinguishes_outdoor_venues():
    """
    The reason the conversion exists: a non-empty string is truthy, so
    an unconverted 'false' makes every venue read as indoor.
    """
    venues = ld.load_venues()
    assert venues['MSG']['indoor'] is True
    assert venues['BMOFIELD']['indoor'] is False
    indoor = [v for v in venues.values() if v['indoor']]
    assert 0 < len(indoor) < len(venues)


def test_load_venues_capacity_compares_numerically():
    # '9000' > '19812' is True as text, which silently mis-sorts any
    # ranking built on the raw CSV values.
    venues = ld.load_venues()
    assert venues['MSG']['capacity'] == 19812
    assert venues['BARCLAYS']['capacity'] < venues['MSG']['capacity']


def test_load_venues_does_not_mutate_the_source_row():
    row = {
        'venue_id': 'X', 'name': 'X', 'city': 'X', 'state_code': 'XX',
        'country_code': 'US', 'capacity': '100', 'opened_year': '2000',
        'latitude': '1.5', 'longitude': '2.5', 'indoor': 'true',
    }
    typed = ld.typed_venue(row)
    assert typed['capacity'] == 100
    assert row['capacity'] == '100'


@pytest.mark.parametrize('field,bad_value', [
    ('capacity', ''),
    ('capacity', 'many'),
    ('opened_year', '19x8'),
    ('latitude', 'north'),
    ('longitude', ''),
    ('indoor', 'maybe'),
    ('indoor', ''),
])
def test_typed_venue_rejects_bad_values(field, bad_value):
    row = {
        'venue_id': 'BAD', 'name': 'X', 'city': 'X', 'state_code': 'XX',
        'country_code': 'US', 'capacity': '100', 'opened_year': '2000',
        'latitude': '1.5', 'longitude': '2.5', 'indoor': 'true',
    }
    row[field] = bad_value
    with pytest.raises(ValueError) as err:
        ld.typed_venue(row)
    # The message has to name the venue and the field, or a typo in a
    # 16-row CSV means hunting for which row broke.
    assert 'BAD' in str(err.value)
    assert field in str(err.value)


@pytest.mark.parametrize('raw,expected', [
    ('true', True), ('TRUE', True), ('Yes', True), ('1', True),
    ('false', False), ('FALSE', False), ('no', False), ('0', False),
    (' true ', True),
])
def test_typed_venue_boolean_spellings(raw, expected):
    row = {
        'venue_id': 'X', 'name': 'X', 'city': 'X', 'state_code': 'XX',
        'country_code': 'US', 'capacity': '100', 'opened_year': '2000',
        'latitude': '1.5', 'longitude': '2.5', 'indoor': raw,
    }
    assert ld.typed_venue(row)['indoor'] is expected
