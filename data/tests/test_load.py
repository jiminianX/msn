import pytest

import data.db_connect as dbc
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
    venues = ld.load_venues_from_csv()
    assert isinstance(venues, dict)
    assert len(venues) > 10
    assert 'MSG' in venues
    assert venues['MSG']['name'] == 'Madison Square Garden'


def test_load_venues_has_every_documented_field():
    for venue_id, venue in ld.load_venues_from_csv().items():
        for field in VENUE_FIELDS:
            assert field in venue, f'{venue_id} is missing {field}'
            assert venue[field] != '', f'{venue_id} has an empty {field}'


def test_load_venues_coordinates_are_usable():
    # The geo utilities float() these, so a bad row would only
    # surface as a ValueError deep inside a distance calculation.
    for venue_id, venue in ld.load_venues_from_csv().items():
        latitude = float(venue['latitude'])
        longitude = float(venue['longitude'])
        assert -90 <= latitude <= 90, venue_id
        assert -180 <= longitude <= 180, venue_id


def test_load_venues_covers_both_countries():
    countries = {v['country_code'] for v in ld.load_venues_from_csv().values()}
    assert countries == {'US', 'CA'}


def test_get_venue(mongo_venues):
    venue = ld.get_venue('msg')
    assert venue['city'] == 'New York'
    assert venue['state_code'] == 'NY'
    assert ld.get_venue('MSG') == venue


def test_get_venue_not_found(mongo_venues):
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
    for venue_id, venue in ld.load_venues_from_csv().items():
        for field, expected in VENUE_FIELD_TYPES.items():
            assert isinstance(venue[field], expected), (
                f'{venue_id}.{field} is {type(venue[field]).__name__}, '
                f'expected {expected.__name__}')


def test_load_venues_indoor_distinguishes_outdoor_venues():
    """
    The reason the conversion exists: a non-empty string is truthy, so
    an unconverted 'false' makes every venue read as indoor.
    """
    venues = ld.load_venues_from_csv()
    assert venues['MSG']['indoor'] is True
    assert venues['BMOFIELD']['indoor'] is False
    indoor = [v for v in venues.values() if v['indoor']]
    assert 0 < len(indoor) < len(venues)


def test_load_venues_capacity_compares_numerically():
    # '9000' > '19812' is True as text, which silently mis-sorts any
    # ranking built on the raw CSV values.
    venues = ld.load_venues_from_csv()
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


# --- the Mongo-backed read path -------------------------------------
#
# load_venues() reads the venues collection, so these exercise that
# path against an in-memory store. No mongod is needed, and the live
# round trip stays covered by the RUN_DB_INTEGRATION test in
# states/tests/test_fancier.py.


class PingableAdmin:
    def command(self, name, **kwargs):
        return {'ok': 1}


class StoredCollection:
    def __init__(self, docs):
        self._docs = docs

    def find(self, filt=None):
        # Fresh copies on purpose. db_connect.read() deletes _id from
        # each document it is handed, so returning the stored dicts
        # would make a second read raise KeyError. Real pymongo decodes
        # new dicts per call, so copying is the faithful behaviour.
        docs = [dict(doc) for doc in self._docs]
        if filt:
            docs = [doc for doc in docs
                    if all(doc.get(k) == v for k, v in filt.items())]
        return docs

    def insert_one(self, doc):
        stored = dict(doc)
        stored[dbc.MONGO_ID] = len(self._docs) + 1
        self._docs.append(stored)
        # Real pymongo mutates the dict it is given by setting _id on
        # it. Mimicking that is what makes the "no _id in the returned
        # record" test meaningful rather than vacuous.
        doc[dbc.MONGO_ID] = stored[dbc.MONGO_ID]
        return stored

    def delete_one(self, filt):
        for index, doc in enumerate(self._docs):
            if all(doc.get(k) == v for k, v in filt.items()):
                del self._docs[index]
                return StoredDeleteResult(1)
        return StoredDeleteResult(0)


class StoredDeleteResult:
    def __init__(self, deleted_count):
        self.deleted_count = deleted_count


class StoredDB:
    def __init__(self, docs):
        self._docs = docs

    def __getitem__(self, collection):
        if collection == ld.VENUES_COLLECTION:
            return StoredCollection(self._docs)
        return StoredCollection([])


class StoredClient:
    def __init__(self, docs):
        self._docs = docs
        self.admin = PingableAdmin()

    def __getitem__(self, db):
        return StoredDB(self._docs)


@pytest.fixture
def mongo_venues(monkeypatch):
    """
    Serve the venues collection from an in-memory store seeded with the
    CSV, which is what `make seed` does against a real database.
    """
    docs = []
    for number, venue in enumerate(
            ld.load_venues_from_csv().values(), start=1):
        doc = dict(venue)
        doc[dbc.MONGO_ID] = number
        docs.append(doc)
    client = StoredClient(docs)
    monkeypatch.delenv('CLOUD_MONGO', raising=False)
    monkeypatch.setattr(dbc, 'client', None)
    monkeypatch.setattr(dbc.pm, 'MongoClient', lambda *a, **kw: client)
    return client


@pytest.fixture
def mongo_down(monkeypatch):
    monkeypatch.setattr(dbc, 'is_db_up', lambda: False)


def test_load_venues_reads_the_collection(mongo_venues):
    venues = ld.load_venues()
    assert len(venues) == 16
    assert venues['MSG']['name'] == 'Madison Square Garden'


def test_load_venues_strips_the_mongo_id(mongo_venues):
    """
    `_id` is an ObjectId in a real database and is not JSON
    serializable, so it must not reach the API response.
    """
    for venue in ld.load_venues().values():
        assert dbc.MONGO_ID not in venue


def test_load_venues_can_be_read_twice(mongo_venues):
    """
    read() deletes _id from each document as it goes. If that mutated
    stored state, the second call would fail -- so this pins that
    reading is not destructive.
    """
    assert ld.load_venues() == ld.load_venues()


def test_load_venues_raises_when_the_database_is_down(mongo_down):
    with pytest.raises(dbc.DatabaseDown) as err:
        ld.load_venues()
    assert 'not reachable' in str(err.value)


def test_get_venue_raises_when_the_database_is_down(mongo_down):
    """
    get_venue() resolves load_venues through the module namespace, so
    it inherits the same failure rather than quietly returning None --
    which would be indistinguishable from 'no such venue'.
    """
    with pytest.raises(dbc.DatabaseDown):
        ld.get_venue('MSG')


def test_csv_loader_still_works_when_the_database_is_down(mongo_down):
    """
    The CSV path is the seed source and must not depend on Mongo,
    otherwise `make seed` could never run against an empty database.
    """
    assert len(ld.load_venues_from_csv()) == 16


# --- creating a venue -----------------------------------------------

NEW_VENUE = {
    'venue_id': 'YANKEE',
    'name': 'Yankee Stadium',
    'city': 'New York',
    'state_code': 'NY',
    'country_code': 'US',
    'capacity': 46537,
    'opened_year': 2009,
    'latitude': 40.8296,
    'longitude': -73.9262,
    'indoor': False,
}


def a_venue(**overrides):
    """
    Return a valid payload, with any field replaced or removed.

    Passing None removes the field, which is how the missing-field
    cases are written without repeating the whole dict each time.
    """
    payload = dict(NEW_VENUE)
    for field, value in overrides.items():
        if value is None:
            payload.pop(field, None)
        else:
            payload[field] = value
    return payload


def test_create_venue_stores_and_returns_the_record(mongo_venues):
    record = ld.create_venue(a_venue())
    assert record['venue_id'] == 'YANKEE'
    assert record['capacity'] == 46537
    assert ld.load_venues()['YANKEE']['name'] == 'Yankee Stadium'


def test_create_venue_returns_a_record_without_a_mongo_id(mongo_venues):
    """
    insert_one sets _id on the dict it is given, and an ObjectId is
    not JSON serializable -- so the driver gets a copy and the caller
    gets a record it can return straight over HTTP.
    """
    record = ld.create_venue(a_venue())
    assert dbc.MONGO_ID not in record


def test_create_venue_does_not_mutate_the_payload(mongo_venues):
    payload = a_venue(venue_id='yankee')
    ld.create_venue(payload)
    assert payload['venue_id'] == 'yankee'
    assert dbc.MONGO_ID not in payload


def test_create_venue_upper_cases_the_id(mongo_venues):
    """
    get_venue() upper-cases its lookup, so a lower-case id would be
    stored but unreachable through GET /venues/<id>.
    """
    record = ld.create_venue(a_venue(venue_id='yankee'))
    assert record['venue_id'] == 'YANKEE'
    assert ld.get_venue('yankee') is not None
    assert ld.get_venue('YANKEE') is not None


def test_create_venue_rejects_a_duplicate_id(mongo_venues):
    ld.create_venue(a_venue())
    with pytest.raises(ld.VenueExists) as err:
        ld.create_venue(a_venue())
    assert 'YANKEE' in str(err.value)


def test_create_venue_rejects_a_duplicate_in_any_case(mongo_venues):
    ld.create_venue(a_venue())
    with pytest.raises(ld.VenueExists):
        ld.create_venue(a_venue(venue_id='yankee'))


def test_create_venue_rejects_an_existing_seeded_id(mongo_venues):
    with pytest.raises(ld.VenueExists):
        ld.create_venue(a_venue(venue_id='MSG'))


def test_create_venue_raises_when_the_database_is_down(mongo_down):
    with pytest.raises(dbc.DatabaseDown):
        ld.create_venue(a_venue())


@pytest.mark.parametrize('field', ld.VENUE_FIELDS)
def test_create_venue_requires_every_documented_field(field, mongo_venues):
    with pytest.raises(ValueError) as err:
        ld.create_venue(a_venue(**{field: None}))
    assert field in str(err.value)


def test_create_venue_rejects_unknown_fields(mongo_venues):
    """
    A misspelled key must fail rather than being dropped, or the venue
    is stored with a stray field and a missing real one.
    """
    payload = a_venue()
    payload['capcity'] = 46537
    with pytest.raises(ValueError) as err:
        ld.create_venue(payload)
    assert 'capcity' in str(err.value)


@pytest.mark.parametrize('payload', [
    None, 'a string', 42, ['a', 'list'],
])
def test_create_venue_rejects_a_non_object_body(payload, mongo_venues):
    with pytest.raises(ValueError):
        ld.create_venue(payload)


@pytest.mark.parametrize('field,bad_value', [
    ('latitude', 200.0),
    ('latitude', -91),
    ('longitude', 181),
    ('latitude', 'north'),
    ('capacity', -5),
    ('capacity', 'many'),
    ('opened_year', 1200),
    ('opened_year', '19x8'),
    ('indoor', 'maybe'),
    ('name', ''),
    ('name', '   '),
    ('city', ''),
    ('venue_id', ''),
    ('state_code', ''),
    ('country_code', ''),
])
def test_create_venue_rejects_bad_values(field, bad_value, mongo_venues):
    with pytest.raises(ValueError):
        ld.create_venue(a_venue(**{field: bad_value}))


def test_create_venue_trims_surrounding_whitespace(mongo_venues):
    record = ld.create_venue(a_venue(name='  Yankee Stadium  '))
    assert record['name'] == 'Yankee Stadium'


def test_nothing_is_stored_when_validation_fails(mongo_venues):
    """
    Validation runs before the connection check and the insert, so a
    rejected payload must leave the collection exactly as it was.
    """
    before = len(ld.load_venues())
    with pytest.raises(ValueError):
        ld.create_venue(a_venue(latitude=200.0))
    assert len(ld.load_venues()) == before


def test_a_created_venue_is_usable_by_the_geo_utilities(mongo_venues):
    """
    The point of validating on write: everything in the collection
    stays safe to hand to the geo package afterwards.
    """
    from geo.capacity import rank_venues_by_capacity
    from geo.nearest import nearest_venue
    ld.create_venue(a_venue())
    venues = list(ld.load_venues().values())
    assert len(rank_venues_by_capacity(venues)) == len(venues)
    assert nearest_venue(40.83, -73.93, venues)['venue'][
        'venue_id'] == 'YANKEE'


# --- deleting a venue -----------------------------------------------


def test_delete_venue_removes_it(mongo_venues):
    assert ld.delete_venue('MSG') is True
    assert 'MSG' not in ld.load_venues()
    assert len(ld.load_venues()) == 15


def test_delete_venue_is_case_insensitive(mongo_venues):
    assert ld.delete_venue('msg') is True
    assert 'MSG' not in ld.load_venues()


def test_delete_venue_tolerates_surrounding_whitespace(mongo_venues):
    assert ld.delete_venue('  msg  ') is True
    assert 'MSG' not in ld.load_venues()


def test_delete_venue_reports_an_unknown_id(mongo_venues):
    assert ld.delete_venue('NOPE') is False
    assert len(ld.load_venues()) == 16


@pytest.mark.parametrize('venue_id', [None, '', '   ', 17, ['MSG']])
def test_delete_venue_reports_a_bad_id(venue_id, mongo_venues):
    assert ld.delete_venue(venue_id) is False
    assert len(ld.load_venues()) == 16


def test_delete_venue_removes_only_one(mongo_venues):
    before = set(ld.load_venues())
    ld.delete_venue('MSG')
    assert before - set(ld.load_venues()) == {'MSG'}


def test_delete_venue_raises_when_the_database_is_down(mongo_down):
    with pytest.raises(dbc.DatabaseDown):
        ld.delete_venue('MSG')


def test_create_then_delete_round_trip(mongo_venues):
    """
    The pair is what makes either one testable without residue: a
    create can be undone, so a test need not leave a document behind
    to prove the write worked.
    """
    ld.create_venue(a_venue())
    assert 'YANKEE' in ld.load_venues()
    assert ld.delete_venue('YANKEE') is True
    assert 'YANKEE' not in ld.load_venues()
    assert len(ld.load_venues()) == 16


def test_an_id_can_be_reused_after_deletion(mongo_venues):
    """
    The duplicate check reads the collection rather than a cache, so a
    deleted id must become available again.
    """
    ld.create_venue(a_venue())
    ld.delete_venue('YANKEE')
    ld.create_venue(a_venue())
    assert 'YANKEE' in ld.load_venues()


def test_delete_clears_a_poisoned_document(mongo_venues):
    """
    The operational reason delete exists. A document with an
    out-of-range latitude -- however it got there -- breaks
    nearest_venue for every caller, and this is now the supported way
    to remove it.
    """
    from geo.nearest import nearest_venue
    bad = dict(NEW_VENUE)
    bad['latitude'] = 200.0
    dbc.create(ld.VENUES_COLLECTION, bad)
    with pytest.raises(ValueError):
        nearest_venue(40.7, -74.0, list(ld.load_venues().values()))
    assert ld.delete_venue('YANKEE') is True
    assert nearest_venue(
        40.7, -74.0, list(ld.load_venues().values())) is not None


def test_load_teams():
    teams = ld.load_teams()
    assert len(teams) == 16
    assert teams['NYK']['name'] == 'New York Knicks'
    assert teams['NYK']['venue_id'] == 'MSG'
    assert teams['NYK']['founded_year'] == 1946


def test_load_teams_types():
    for team in ld.load_teams().values():
        assert isinstance(team['founded_year'], int)


def test_every_team_links_to_a_known_league_and_venue():
    leagues = ld.load_leagues()
    venues = ld.load_venues_from_csv()
    for team_id, team in ld.load_teams().items():
        assert team['league_code'] in leagues, team_id
        assert team['venue_id'] in venues, team_id


def test_mls_teams_have_no_division():
    mls = [t for t in ld.load_teams().values() if t['league_code'] == 'MLS']
    assert mls
    assert all(t['division'] == '' for t in mls)


def test_get_team():
    team = ld.get_team('nyk')
    assert team['name'] == 'New York Knicks'
    assert ld.get_team(' NYK ') == team


def test_get_team_not_found():
    assert ld.get_team('XYZ') is None
    assert ld.get_team(None) is None


def test_typed_team_rejects_bad_year():
    with pytest.raises(ValueError):
        ld.typed_team({'team_id': 'BAD', 'founded_year': 'soon'})
