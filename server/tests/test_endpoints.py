from http import HTTPStatus

import pytest

import data.db_connect as dbc
import data.load as data_load
import server.endpoints as ep

TEST_CLIENT = ep.app.test_client()


def test_hello():
    resp = TEST_CLIENT.get(ep.HELLO_EP)
    resp_json = resp.get_json()
    assert ep.HELLO_RESP in resp_json


def test_endpoints():
    resp = TEST_CLIENT.get(ep.ENDPOINT_EP)
    assert resp.status_code == HTTPStatus.OK
    resp_json = resp.get_json()
    assert ep.ENDPOINT_RESP in resp_json
    endpoints = resp_json[ep.ENDPOINT_RESP]
    assert isinstance(endpoints, list)
    assert ep.HELLO_EP in endpoints


def test_get_states():
    resp = TEST_CLIENT.get(ep.STATES_EP)
    resp_json = resp.get_json()
    assert ep.STATES_RESP in resp_json
    assert isinstance(resp_json[ep.STATES_RESP], dict)


def test_get_state():
    resp = TEST_CLIENT.get(f'{ep.STATES_EP}/AL')
    assert resp.status_code == HTTPStatus.OK
    resp_json = resp.get_json()
    assert resp_json[ep.STATE_RESP]['name'] == 'Alabama'
    assert resp_json[ep.STATE_RESP]['capital'] == 'Montgomery'


def test_get_state_not_found():
    resp = TEST_CLIENT.get(f'{ep.STATES_EP}/ZZ')
    assert resp.status_code == HTTPStatus.NOT_FOUND


def test_get_countries():
    response = TEST_CLIENT.get(ep.COUNTRIES_EP)

    assert response.status_code == 200

    countries = response.get_json()[ep.COUNTRIES_RESP]
    assert "US" in countries
    assert "CA" in countries
    assert countries["US"]["name"] == "United States"
    assert countries["CA"]["name"] == "Canada"


def test_get_leagues():
    response = TEST_CLIENT.get(ep.LEAGUES_EP)

    assert response.status_code == 200

    leagues = response.get_json()[ep.LEAGUES_RESP]
    assert "NBA" in leagues
    assert "MLS" in leagues
    assert leagues["NBA"]["sport"] == "Basketball"
    assert leagues["MLS"]["sport"] == "Soccer"


def test_get_country():
    resp = TEST_CLIENT.get(f'{ep.COUNTRIES_EP}/US')
    assert resp.status_code == HTTPStatus.OK
    assert resp.get_json()[ep.COUNTRY_RESP]['name'] == 'United States'


def test_get_country_case_insensitive():
    resp = TEST_CLIENT.get(f'{ep.COUNTRIES_EP}/ca')
    assert resp.status_code == HTTPStatus.OK
    assert resp.get_json()[ep.COUNTRY_RESP]['name'] == 'Canada'


def test_get_country_not_found():
    resp = TEST_CLIENT.get(f'{ep.COUNTRIES_EP}/ZZ')
    assert resp.status_code == HTTPStatus.NOT_FOUND


def test_get_league():
    resp = TEST_CLIENT.get(f'{ep.LEAGUES_EP}/NBA')
    assert resp.status_code == HTTPStatus.OK
    assert resp.get_json()[ep.LEAGUE_RESP]['sport'] == 'Basketball'


def test_get_league_case_insensitive():
    resp = TEST_CLIENT.get(f'{ep.LEAGUES_EP}/mls')
    assert resp.status_code == HTTPStatus.OK
    assert resp.get_json()[ep.LEAGUE_RESP]['sport'] == 'Soccer'


def test_get_league_not_found():
    resp = TEST_CLIENT.get(f'{ep.LEAGUES_EP}/XFL')
    assert resp.status_code == HTTPStatus.NOT_FOUND


NYC_TO_LA = {'lat1': 40.7128, 'lon1': -74.0060,
             'lat2': 34.0522, 'lon2': -118.2437}


def test_get_distance():
    resp = TEST_CLIENT.get(ep.DISTANCE_EP, query_string=NYC_TO_LA)
    assert resp.status_code == HTTPStatus.OK
    miles = resp.get_json()[ep.DISTANCE_RESP]
    assert miles == pytest.approx(2445, abs=10)


def test_get_distance_missing_param():
    params = dict(NYC_TO_LA)
    del params['lon2']
    resp = TEST_CLIENT.get(ep.DISTANCE_EP, query_string=params)
    assert resp.status_code == HTTPStatus.BAD_REQUEST


def test_get_distance_out_of_range():
    params = dict(NYC_TO_LA, lat1=91)
    resp = TEST_CLIENT.get(ep.DISTANCE_EP, query_string=params)
    assert resp.status_code == HTTPStatus.BAD_REQUEST


def test_get_states_db_down(monkeypatch):
    monkeypatch.setattr(ep.sqry, 'get_states', lambda: None)
    resp = TEST_CLIENT.get(ep.STATES_EP)
    assert resp.status_code == HTTPStatus.SERVICE_UNAVAILABLE


@pytest.mark.parametrize(
    'invalid_value',
    ['hello', 'NaN', 'inf', '-inf'],
)
def test_get_distance_non_numeric_or_nonfinite(invalid_value):
    params = dict(NYC_TO_LA, lat1=invalid_value)
    resp = TEST_CLIENT.get(ep.DISTANCE_EP, query_string=params)
    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.parametrize('invalid_lon', [-181, 181])
def test_get_distance_invalid_longitude(invalid_lon):
    params = dict(NYC_TO_LA, lon1=invalid_lon)
    resp = TEST_CLIENT.get(ep.DISTANCE_EP, query_string=params)
    assert resp.status_code == HTTPStatus.BAD_REQUEST


def test_get_distance_same_coordinates():
    params = {
        'lat1': 40.7128,
        'lon1': -74.0060,
        'lat2': 40.7128,
        'lon2': -74.0060,
    }
    resp = TEST_CLIENT.get(ep.DISTANCE_EP, query_string=params)
    assert resp.status_code == HTTPStatus.OK
    assert resp.get_json()[ep.DISTANCE_RESP] == pytest.approx(0)


MSG = {'latitude': 40.7505, 'longitude': -73.9934}
TD_GARDEN = {'latitude': 42.3662, 'longitude': -71.0621}
SCOTIABANK = {'latitude': 43.6435, 'longitude': -79.3791}


def test_post_road_trip():
    resp = TEST_CLIENT.post(ep.ROAD_TRIP_EP,
                            json={ep.ROAD_TRIP_VENUES: [MSG, TD_GARDEN]})
    assert resp.status_code == HTTPStatus.OK
    miles = resp.get_json()[ep.ROAD_TRIP_RESP]
    assert miles == pytest.approx(187.5, abs=1.0)


def test_post_road_trip_multiple_legs():
    two_legs = {ep.ROAD_TRIP_VENUES: [MSG, TD_GARDEN, SCOTIABANK]}
    one_leg = {ep.ROAD_TRIP_VENUES: [MSG, TD_GARDEN]}
    total = TEST_CLIENT.post(
        ep.ROAD_TRIP_EP, json=two_legs).get_json()[ep.ROAD_TRIP_RESP]
    first = TEST_CLIENT.post(
        ep.ROAD_TRIP_EP, json=one_leg).get_json()[ep.ROAD_TRIP_RESP]
    # Adding a stop can only add mileage.
    assert total > first


@pytest.mark.parametrize('venues', [[], [MSG]])
def test_post_road_trip_no_travel(venues):
    resp = TEST_CLIENT.post(ep.ROAD_TRIP_EP,
                            json={ep.ROAD_TRIP_VENUES: venues})
    assert resp.status_code == HTTPStatus.OK
    assert resp.get_json()[ep.ROAD_TRIP_RESP] == pytest.approx(0)


def test_post_road_trip_accepts_a_venue_record():
    # A row straight out of the venues data carries extra keys;
    # the endpoint must not choke on them.
    record = dict(MSG, venue_id='MSG', name='Madison Square Garden')
    resp = TEST_CLIENT.post(ep.ROAD_TRIP_EP,
                            json={ep.ROAD_TRIP_VENUES: [record, TD_GARDEN]})
    assert resp.status_code == HTTPStatus.OK


@pytest.mark.parametrize('body', [
    {},
    {'stops': [MSG, TD_GARDEN]},
    {ep.ROAD_TRIP_VENUES: 'MSG'},
    {ep.ROAD_TRIP_VENUES: [MSG, 'TD Garden']},
    {ep.ROAD_TRIP_VENUES: [MSG, {'latitude': 42.3662}]},
    {ep.ROAD_TRIP_VENUES: [MSG, {'latitude': 'north', 'longitude': -71.06}]},
    {ep.ROAD_TRIP_VENUES: [MSG, {'latitude': 91, 'longitude': -71.06}]},
])
def test_post_road_trip_bad_request(body):
    resp = TEST_CLIENT.post(ep.ROAD_TRIP_EP, json=body)
    assert resp.status_code == HTTPStatus.BAD_REQUEST


def test_post_road_trip_no_json_body():
    resp = TEST_CLIENT.post(ep.ROAD_TRIP_EP)
    assert resp.status_code == HTTPStatus.BAD_REQUEST


def test_road_trip_is_listed_in_endpoints():
    resp = TEST_CLIENT.get(ep.ENDPOINT_EP)
    assert ep.ROAD_TRIP_EP in resp.get_json()[ep.ENDPOINT_RESP]


def test_get_venues():
    resp = TEST_CLIENT.get(ep.VENUES_EP)
    assert resp.status_code == HTTPStatus.OK
    venues = resp.get_json()[ep.VENUES_RESP]
    assert isinstance(venues, dict)
    assert venues['MSG']['name'] == 'Madison Square Garden'
    assert 'SCOTIABANK' in venues


def test_venues_is_listed_in_endpoints():
    resp = TEST_CLIENT.get(ep.ENDPOINT_EP)
    assert ep.VENUES_EP in resp.get_json()[ep.ENDPOINT_RESP]


def test_get_venue():
    resp = TEST_CLIENT.get(f'{ep.VENUES_EP}/MSG')
    assert resp.status_code == HTTPStatus.OK
    venue = resp.get_json()[ep.VENUE_RESP]
    assert venue['name'] == 'Madison Square Garden'
    assert venue['city'] == 'New York'


def test_get_venue_case_insensitive():
    resp = TEST_CLIENT.get(f'{ep.VENUES_EP}/tdgarden')
    assert resp.status_code == HTTPStatus.OK
    assert resp.get_json()[ep.VENUE_RESP]['state_code'] == 'MA'


def test_get_venue_not_found():
    resp = TEST_CLIENT.get(f'{ep.VENUES_EP}/NOPE')
    assert resp.status_code == HTTPStatus.NOT_FOUND


def test_get_distance_reports_every_missing_param():
    resp = TEST_CLIENT.get(ep.DISTANCE_EP, query_string={'lat1': 40.7})
    assert resp.status_code == HTTPStatus.BAD_REQUEST
    message = resp.get_json()['message']
    for name in ('lon1', 'lat2', 'lon2'):
        assert name in message


TIMES_SQUARE = {'lat': 40.7580, 'lon': -73.9855}


def test_get_nearest_venue():
    resp = TEST_CLIENT.get(ep.NEAREST_EP, query_string=TIMES_SQUARE)
    assert resp.status_code == HTTPStatus.OK
    result = resp.get_json()[ep.NEAREST_RESP]
    assert result['venue']['venue_id'] == 'MSG'
    assert result['distance_miles'] == pytest.approx(0.6, abs=0.2)


def test_get_nearest_venue_in_canada():
    resp = TEST_CLIENT.get(ep.NEAREST_EP,
                           query_string={'lat': 45.56, 'lon': -73.55})
    assert resp.status_code == HTTPStatus.OK
    assert resp.get_json()[ep.NEAREST_RESP]['venue']['venue_id'] == 'SAPUTO'


def test_nearest_is_not_mistaken_for_a_venue_id():
    # /venues/<venue_id> must not swallow the static /venues/nearest route.
    resp = TEST_CLIENT.get(ep.NEAREST_EP)
    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.parametrize('params', [
    {'lat': 40.7580},
    {'lat': 'north', 'lon': -73.9855},
    {'lat': 91, 'lon': -73.9855},
    {'lat': 40.7580, 'lon': 'inf'},
])
def test_get_nearest_venue_bad_request(params):
    resp = TEST_CLIENT.get(ep.NEAREST_EP, query_string=params)
    assert resp.status_code == HTTPStatus.BAD_REQUEST


def test_get_venues_by_capacity():
    resp = TEST_CLIENT.get(ep.BY_CAPACITY_EP)
    assert resp.status_code == HTTPStatus.OK
    ranked = resp.get_json()[ep.BY_CAPACITY_RESP]
    assert isinstance(ranked, list)
    assert len(ranked) == len(TEST_CLIENT.get(
        ep.VENUES_EP).get_json()[ep.VENUES_RESP])
    capacities = [int(venue['capacity']) for venue in ranked]
    assert capacities == sorted(capacities, reverse=True)


def test_get_venues_by_capacity_filtered_by_state():
    resp = TEST_CLIENT.get(ep.BY_CAPACITY_EP, query_string={'state': 'ny'})
    assert resp.status_code == HTTPStatus.OK
    ranked = resp.get_json()[ep.BY_CAPACITY_RESP]
    assert [venue['venue_id'] for venue in ranked] == ['MSG', 'BARCLAYS']


def test_get_venues_by_capacity_unknown_state():
    resp = TEST_CLIENT.get(ep.BY_CAPACITY_EP, query_string={'state': 'ZZ'})
    assert resp.status_code == HTTPStatus.OK
    assert resp.get_json()[ep.BY_CAPACITY_RESP] == []


def test_get_venues_by_capacity_filtered_by_country():
    resp = TEST_CLIENT.get(ep.BY_CAPACITY_EP,
                           query_string={ep.BY_CAPACITY_COUNTRY: 'CA'})
    assert resp.status_code == HTTPStatus.OK
    ranked = resp.get_json()[ep.BY_CAPACITY_RESP]
    assert [venue['venue_id'] for venue in ranked] == [
        'BCPLACE', 'BMOFIELD', 'SCOTIABANK', 'SAPUTO']


def test_get_venues_by_capacity_country_is_case_insensitive():
    resp = TEST_CLIENT.get(ep.BY_CAPACITY_EP,
                           query_string={ep.BY_CAPACITY_COUNTRY: 'ca'})
    assert resp.status_code == HTTPStatus.OK
    assert len(resp.get_json()[ep.BY_CAPACITY_RESP]) == 4


def test_get_venues_by_capacity_unknown_country():
    resp = TEST_CLIENT.get(ep.BY_CAPACITY_EP,
                           query_string={ep.BY_CAPACITY_COUNTRY: 'ZZ'})
    assert resp.status_code == HTTPStatus.OK
    assert resp.get_json()[ep.BY_CAPACITY_RESP] == []


def test_country_and_state_codes_do_not_collide():
    """
    CA is both California's state code and Canada's country code, so
    the two filters have to be judged separately rather than against a
    single shared code.
    """
    by_country = TEST_CLIENT.get(
        ep.BY_CAPACITY_EP,
        query_string={ep.BY_CAPACITY_COUNTRY: 'CA'},
    ).get_json()[ep.BY_CAPACITY_RESP]
    by_state = TEST_CLIENT.get(
        ep.BY_CAPACITY_EP,
        query_string={ep.BY_CAPACITY_STATE: 'CA'},
    ).get_json()[ep.BY_CAPACITY_RESP]
    assert {venue['country_code'] for venue in by_country} == {'CA'}
    assert {venue['state_code'] for venue in by_state} == {'CA'}
    assert {venue['venue_id'] for venue in by_country}.isdisjoint(
        venue['venue_id'] for venue in by_state)


def test_get_venues_by_capacity_limit():
    resp = TEST_CLIENT.get(ep.BY_CAPACITY_EP,
                           query_string={ep.BY_CAPACITY_LIMIT: '3'})
    assert resp.status_code == HTTPStatus.OK
    ranked = resp.get_json()[ep.BY_CAPACITY_RESP]
    assert [venue['venue_id'] for venue in ranked] == [
        'BCPLACE', 'BMOFIELD', 'PROVIDENCE']


def test_get_venues_by_capacity_limit_above_the_venue_count():
    resp = TEST_CLIENT.get(ep.BY_CAPACITY_EP,
                           query_string={ep.BY_CAPACITY_LIMIT: '500'})
    assert resp.status_code == HTTPStatus.OK
    ranked = resp.get_json()[ep.BY_CAPACITY_RESP]
    assert len(ranked) == len(TEST_CLIENT.get(
        ep.VENUES_EP).get_json()[ep.VENUES_RESP])


def test_get_venues_by_capacity_filters_combine():
    resp = TEST_CLIENT.get(ep.BY_CAPACITY_EP, query_string={
        ep.BY_CAPACITY_COUNTRY: 'CA',
        ep.BY_CAPACITY_LIMIT: '2',
    })
    assert resp.status_code == HTTPStatus.OK
    ranked = resp.get_json()[ep.BY_CAPACITY_RESP]
    assert [venue['venue_id'] for venue in ranked] == ['BCPLACE', 'BMOFIELD']


@pytest.mark.parametrize('bad_limit', ['two', '', '1.5', '0', '-3'])
def test_get_venues_by_capacity_bad_limit(bad_limit):
    resp = TEST_CLIENT.get(ep.BY_CAPACITY_EP,
                           query_string={ep.BY_CAPACITY_LIMIT: bad_limit})
    assert resp.status_code == HTTPStatus.BAD_REQUEST


# --- the venue endpoints when MongoDB is unreachable ----------------
#
# conftest.py serves these tests from the CSV so the rest of the suite
# does not need a database. These override that in the other
# direction, which is the whole reason the loader is patched at a seam
# rather than faked wholesale.

VENUE_READ_ENDPOINTS = [
    ep.VENUES_EP,
    f'{ep.VENUES_EP}/MSG',
    ep.NEAREST_EP,
    ep.BY_CAPACITY_EP,
]


@pytest.fixture
def db_down(monkeypatch):
    def raise_down():
        raise dbc.DatabaseDown(
            'MongoDB is not reachable; venue data is unavailable.')
    monkeypatch.setattr(data_load, 'load_venues', raise_down)


@pytest.mark.parametrize('endpoint', VENUE_READ_ENDPOINTS)
def test_venue_endpoints_are_unavailable_when_the_db_is_down(
        endpoint, db_down):
    query = {'lat': '40.75', 'lon': '-73.99'}
    resp = TEST_CLIENT.get(endpoint, query_string=query)
    assert resp.status_code == HTTPStatus.SERVICE_UNAVAILABLE


def test_unavailable_response_explains_itself(db_down):
    """
    503 with no message leaves the caller guessing between a crash and
    a missing dependency, so the reason travels with the status.
    """
    resp = TEST_CLIENT.get(ep.VENUES_EP)
    assert 'MongoDB' in resp.get_data(as_text=True)


def test_bad_request_still_wins_over_unavailable(db_down):
    """
    Argument validation runs before the read, so a malformed request
    against a down database is still a 400. Were this a 503, a client
    would retry a request that can never succeed.
    """
    resp = TEST_CLIENT.get(ep.NEAREST_EP, query_string={'lat': '40.75'})
    assert resp.status_code == HTTPStatus.BAD_REQUEST


def test_endpoints_not_backed_by_mongo_still_answer(db_down):
    """
    Countries, leagues and the pure geometry endpoints read CSVs or
    nothing at all, so a down database must not take them with it.
    """
    assert TEST_CLIENT.get(ep.COUNTRIES_EP).status_code == HTTPStatus.OK
    assert TEST_CLIENT.get(ep.LEAGUES_EP).status_code == HTTPStatus.OK
    assert TEST_CLIENT.get(ep.HELLO_EP).status_code == HTTPStatus.OK
    distance = TEST_CLIENT.get(ep.DISTANCE_EP, query_string={
        'lat1': '40.75', 'lon1': '-73.99',
        'lat2': '34.04', 'lon2': '-118.27'})
    assert distance.status_code == HTTPStatus.OK


def test_the_decorator_is_applied_to_every_venue_read():
    """
    A fifth venue endpoint added without the decorator would answer
    500 instead of 503, and no existing test would notice. This fails
    the moment one is missing.
    """
    for resource in (ep.Venues, ep.Venue, ep.NearestVenue,
                     ep.VenuesByCapacity):
        assert hasattr(resource.get, '__wrapped__'), resource.__name__


# --- POST /venues ---------------------------------------------------

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
    payload = dict(NEW_VENUE)
    for field, value in overrides.items():
        if value is None:
            payload.pop(field, None)
        else:
            payload[field] = value
    return payload


@pytest.fixture
def venue_store(monkeypatch):
    """
    Store created venues in a dict instead of MongoDB.

    Only the storage call is replaced -- `validated_venue` still runs,
    so every 400 in these tests is produced by the same validation a
    real request meets. The database-level behaviour (the duplicate
    lookup, insert_one's _id mutation, DatabaseDown) is covered
    against a fake client in data/tests/test_load.py.

    This also keeps the suite from writing into a real database in
    RUN_DB_INTEGRATION mode, where the autouse fixture steps aside.
    """
    stored = {}

    def fake_create(payload):
        record = data_load.validated_venue(payload)
        venue_id = record[data_load.VENUE_ID]
        if venue_id in stored:
            raise data_load.VenueExists(
                f'a venue with id {venue_id!r} already exists')
        stored[venue_id] = record
        return record

    monkeypatch.setattr(data_load, 'create_venue', fake_create)
    return stored


def test_post_venue_creates_it(venue_store):
    resp = TEST_CLIENT.post(ep.VENUES_EP, json=a_venue())
    assert resp.status_code == HTTPStatus.CREATED
    venue = resp.get_json()[ep.VENUE_RESP]
    assert venue['venue_id'] == 'YANKEE'
    assert venue['capacity'] == 46537
    assert venue['indoor'] is False
    assert 'YANKEE' in venue_store


def test_post_venue_returns_a_location_header(venue_store):
    """
    A 201 should say where the thing it made now lives, so a client
    does not have to assemble the URL itself.
    """
    resp = TEST_CLIENT.post(ep.VENUES_EP, json=a_venue())
    assert resp.headers['Location'].endswith(f'{ep.VENUES_EP}/YANKEE')


def test_post_venue_response_is_json_serializable(venue_store):
    """
    An ObjectId would blow up here, which is why create_venue hands
    the driver a copy rather than the record it returns.
    """
    resp = TEST_CLIENT.post(ep.VENUES_EP, json=a_venue())
    assert ep.dbc.MONGO_ID not in resp.get_json()[ep.VENUE_RESP]


def test_post_duplicate_venue_is_a_conflict(venue_store):
    TEST_CLIENT.post(ep.VENUES_EP, json=a_venue())
    resp = TEST_CLIENT.post(ep.VENUES_EP, json=a_venue())
    assert resp.status_code == HTTPStatus.CONFLICT
    assert 'YANKEE' in resp.get_data(as_text=True)


@pytest.mark.parametrize('field', [
    'venue_id', 'name', 'city', 'state_code', 'country_code',
    'capacity', 'opened_year', 'latitude', 'longitude', 'indoor',
])
def test_post_venue_missing_a_field_is_a_bad_request(field, venue_store):
    resp = TEST_CLIENT.post(ep.VENUES_EP, json=a_venue(**{field: None}))
    assert resp.status_code == HTTPStatus.BAD_REQUEST
    assert field in resp.get_data(as_text=True)


@pytest.mark.parametrize('field,bad_value', [
    ('latitude', 200.0),
    ('longitude', 181),
    ('capacity', -5),
    ('capacity', 'many'),
    ('opened_year', 1200),
    ('indoor', 'maybe'),
    ('name', '   '),
])
def test_post_venue_with_a_bad_value_is_a_bad_request(
        field, bad_value, venue_store):
    resp = TEST_CLIENT.post(ep.VENUES_EP, json=a_venue(**{field: bad_value}))
    assert resp.status_code == HTTPStatus.BAD_REQUEST


def test_post_venue_with_an_unknown_field_is_a_bad_request(venue_store):
    payload = a_venue()
    payload['capcity'] = 46537
    resp = TEST_CLIENT.post(ep.VENUES_EP, json=payload)
    assert resp.status_code == HTTPStatus.BAD_REQUEST
    assert 'capcity' in resp.get_data(as_text=True)


@pytest.mark.parametrize('body', [None, 'a string', 42, ['a', 'list']])
def test_post_venue_with_a_non_object_body_is_a_bad_request(
        body, venue_store):
    resp = TEST_CLIENT.post(ep.VENUES_EP, json=body)
    assert resp.status_code == HTTPStatus.BAD_REQUEST


def test_post_venue_with_no_body_is_a_bad_request(venue_store):
    resp = TEST_CLIENT.post(ep.VENUES_EP)
    assert resp.status_code == HTTPStatus.BAD_REQUEST


def test_post_venue_is_unavailable_when_the_db_is_down(monkeypatch):
    def raise_down(payload):
        raise dbc.DatabaseDown(
            'MongoDB is not reachable; the venue was not created.')
    monkeypatch.setattr(data_load, 'create_venue', raise_down)
    resp = TEST_CLIENT.post(ep.VENUES_EP, json=a_venue())
    assert resp.status_code == HTTPStatus.SERVICE_UNAVAILABLE


def test_a_rejected_post_cannot_poison_the_read_endpoints(venue_store):
    """
    The reason this endpoint validates at all.

    Inserting a venue with latitude 200 directly into MongoDB makes
    /venues/nearest and /venues/by_capacity answer 400 to every
    caller until it is removed. A POST must not be able to do that.
    """
    resp = TEST_CLIENT.post(ep.VENUES_EP, json=a_venue(latitude=200.0))
    assert resp.status_code == HTTPStatus.BAD_REQUEST
    assert venue_store == {}
    assert TEST_CLIENT.get(ep.VENUES_EP).status_code == HTTPStatus.OK
    nearest = TEST_CLIENT.get(ep.NEAREST_EP,
                              query_string={'lat': '40.7', 'lon': '-74.0'})
    assert nearest.status_code == HTTPStatus.OK
    assert TEST_CLIENT.get(
        ep.BY_CAPACITY_EP).status_code == HTTPStatus.OK


def test_get_is_still_a_read_only_route():
    """
    Adding post() to the Venues resource must not change its get().
    """
    resp = TEST_CLIENT.get(ep.VENUES_EP)
    assert resp.status_code == HTTPStatus.OK
    assert len(resp.get_json()[ep.VENUES_RESP]) == 16


# --- DELETE /venues/<venue_id> --------------------------------------


@pytest.fixture
def deletable_venues(monkeypatch):
    """
    Delete from a dict of the CSV venues instead of MongoDB.

    Same reasoning as `venue_store`: these tests are about the
    endpoint's status mapping, and the collection-level behaviour is
    covered against a fake client in data/tests/test_load.py. Keeping
    the write off a real database matters in RUN_DB_INTEGRATION mode,
    where the autouse fixture steps aside.
    """
    remaining = dict(data_load.load_venues_from_csv())

    def fake_delete(venue_id):
        if not isinstance(venue_id, str) or not venue_id.strip():
            return False
        return remaining.pop(venue_id.strip().upper(), None) is not None

    monkeypatch.setattr(data_load, 'delete_venue', fake_delete)
    monkeypatch.setattr(data_load, 'load_venues', lambda: remaining)
    return remaining


def test_delete_venue_removes_it(deletable_venues):
    resp = TEST_CLIENT.delete(f'{ep.VENUES_EP}/MSG')
    assert resp.status_code == HTTPStatus.OK
    assert resp.get_json()[ep.DELETED_RESP] == 'MSG'
    assert 'MSG' not in deletable_venues


def test_delete_venue_is_case_insensitive(deletable_venues):
    resp = TEST_CLIENT.delete(f'{ep.VENUES_EP}/msg')
    assert resp.status_code == HTTPStatus.OK
    assert resp.get_json()[ep.DELETED_RESP] == 'MSG'


def test_delete_unknown_venue_is_not_found(deletable_venues):
    resp = TEST_CLIENT.delete(f'{ep.VENUES_EP}/NOPE')
    assert resp.status_code == HTTPStatus.NOT_FOUND
    assert 'NOPE' in resp.get_data(as_text=True)
    assert len(deletable_venues) == 16


def test_deleted_venue_is_gone_from_the_reads(deletable_venues):
    TEST_CLIENT.delete(f'{ep.VENUES_EP}/MSG')
    listing = TEST_CLIENT.get(ep.VENUES_EP).get_json()[ep.VENUES_RESP]
    assert 'MSG' not in listing
    assert len(listing) == 15
    assert TEST_CLIENT.get(
        f'{ep.VENUES_EP}/MSG').status_code == HTTPStatus.NOT_FOUND


def test_delete_venue_twice_is_not_found_the_second_time(deletable_venues):
    assert TEST_CLIENT.delete(
        f'{ep.VENUES_EP}/MSG').status_code == HTTPStatus.OK
    assert TEST_CLIENT.delete(
        f'{ep.VENUES_EP}/MSG').status_code == HTTPStatus.NOT_FOUND


def test_delete_venue_is_unavailable_when_the_db_is_down(monkeypatch):
    def raise_down(venue_id):
        raise dbc.DatabaseDown(
            'MongoDB is not reachable; the venue was not deleted.')
    monkeypatch.setattr(data_load, 'delete_venue', raise_down)
    resp = TEST_CLIENT.delete(f'{ep.VENUES_EP}/MSG')
    assert resp.status_code == HTTPStatus.SERVICE_UNAVAILABLE


def test_delete_does_not_affect_the_get_on_the_same_route(
        deletable_venues):
    """
    Venue.get and Venue.delete share a resource class, so a 404 from
    one must not be produced by the other.
    """
    assert TEST_CLIENT.get(
        f'{ep.VENUES_EP}/MSG').status_code == HTTPStatus.OK
    TEST_CLIENT.delete(f'{ep.VENUES_EP}/MSG')
    assert TEST_CLIENT.get(
        f'{ep.VENUES_EP}/MSG').status_code == HTTPStatus.NOT_FOUND


def test_both_write_methods_are_wrapped_for_unavailability():
    """
    A write that is not wrapped answers 500 instead of 503 when Mongo
    is gone, and no other test would catch it.
    """
    assert hasattr(ep.Venues.post, '__wrapped__')
    assert hasattr(ep.Venue.delete, '__wrapped__')


def test_get_venues_filtered_by_country():
    resp = TEST_CLIENT.get(
        ep.VENUES_EP, query_string={'country': 'CA'}
    )

    assert resp.status_code == HTTPStatus.OK

    venues = resp.get_json()[ep.VENUES_RESP]
    assert len(venues) > 0
    assert all(v['country_code'] == 'CA' for v in venues.values())


def test_get_venues_country_case_insensitive():
    resp = TEST_CLIENT.get(
        ep.VENUES_EP, query_string={'country': 'ca'}
    )

    assert resp.status_code == HTTPStatus.OK

    venues = resp.get_json()[ep.VENUES_RESP]
    assert len(venues) > 0
    assert all(v['country_code'] == 'CA' for v in venues.values())


def test_get_venues_unknown_country():
    resp = TEST_CLIENT.get(
        ep.VENUES_EP, query_string={'country': 'ZZ'}
    )

    assert resp.status_code == HTTPStatus.OK
    assert resp.get_json()[ep.VENUES_RESP] == {}


def test_get_venues_filtered_by_state():
    resp = TEST_CLIENT.get(
        ep.VENUES_EP, query_string={'state': 'NY'}
    )

    assert resp.status_code == HTTPStatus.OK

    venues = resp.get_json()[ep.VENUES_RESP]
    assert len(venues) > 0
    assert all(v['state_code'] == 'NY' for v in venues.values())


def test_get_venues_state_case_insensitive():
    resp = TEST_CLIENT.get(
        ep.VENUES_EP, query_string={'state': 'ny'}
    )

    assert resp.status_code == HTTPStatus.OK

    venues = resp.get_json()[ep.VENUES_RESP]
    assert len(venues) > 0
    assert all(v['state_code'] == 'NY' for v in venues.values())


def test_get_venues_combined_filters():
    resp = TEST_CLIENT.get(
        ep.VENUES_EP,
        query_string={'country': 'US', 'state': 'NY'}
    )

    assert resp.status_code == HTTPStatus.OK

    venues = resp.get_json()[ep.VENUES_RESP]
    assert len(venues) > 0

    for venue in venues.values():
        assert venue['country_code'] == 'US'
        assert venue['state_code'] == 'NY'


def test_get_venues_filters_return_every_match():
    """
    The filter tests above check that every returned venue matches.
    These pin the full sets, so a filter that silently dropped a
    matching venue would also fail.
    """
    by_country = TEST_CLIENT.get(
        ep.VENUES_EP, query_string={'country': 'CA'}
    ).get_json()[ep.VENUES_RESP]
    assert set(by_country) == {'SCOTIABANK', 'BMOFIELD', 'SAPUTO',
                               'BCPLACE'}

    by_state = TEST_CLIENT.get(
        ep.VENUES_EP, query_string={'state': 'NY'}
    ).get_json()[ep.VENUES_RESP]
    assert set(by_state) == {'MSG', 'BARCLAYS'}


def test_get_venues_unknown_state():
    resp = TEST_CLIENT.get(
        ep.VENUES_EP, query_string={'state': 'ZZ'}
    )

    assert resp.status_code == HTTPStatus.OK
    assert resp.get_json()[ep.VENUES_RESP] == {}


def test_get_venues_state_and_country_are_judged_separately():
    """
    CA is California as a state but Canada as a country. Asking for
    both at once matches no venue rather than mixing the two -- the
    same guarantee /venues/by_capacity already tests.
    """
    resp = TEST_CLIENT.get(
        ep.VENUES_EP, query_string={'country': 'CA', 'state': 'CA'}
    )

    assert resp.status_code == HTTPStatus.OK
    assert resp.get_json()[ep.VENUES_RESP] == {}


def test_get_teams():
    resp = TEST_CLIENT.get(ep.TEAMS_EP)
    assert resp.status_code == HTTPStatus.OK
    teams = resp.get_json()[ep.TEAMS_RESP]
    assert isinstance(teams, dict)
    assert len(teams) == 16
    assert teams['NYK']['venue_id'] == 'MSG'


def test_teams_is_listed_in_endpoints():
    resp = TEST_CLIENT.get(ep.ENDPOINT_EP)
    assert ep.TEAMS_EP in resp.get_json()[ep.ENDPOINT_RESP]


@pytest.mark.parametrize('league', ['NBA', 'mls'])
def test_get_teams_filtered_by_league(league):
    resp = TEST_CLIENT.get(f'{ep.TEAMS_EP}?{ep.TEAMS_LEAGUE}={league}')
    assert resp.status_code == HTTPStatus.OK
    teams = resp.get_json()[ep.TEAMS_RESP]
    assert teams
    assert all(t['league_code'] == league.upper() for t in teams.values())


def test_get_teams_unknown_league_is_empty_not_404():
    resp = TEST_CLIENT.get(f'{ep.TEAMS_EP}?{ep.TEAMS_LEAGUE}=XFL')
    assert resp.status_code == HTTPStatus.OK
    assert resp.get_json()[ep.TEAMS_RESP] == {}


def test_get_team():
    resp = TEST_CLIENT.get(f'{ep.TEAMS_EP}/TFC')
    assert resp.status_code == HTTPStatus.OK
    team = resp.get_json()[ep.TEAM_RESP]
    assert team['name'] == 'Toronto FC'
    assert team['league_code'] == 'MLS'


def test_get_team_case_insensitive():
    upper = TEST_CLIENT.get(f'{ep.TEAMS_EP}/LAL')
    lower = TEST_CLIENT.get(f'{ep.TEAMS_EP}/lal')
    assert lower.status_code == HTTPStatus.OK
    assert upper.get_json() == lower.get_json()


def test_get_team_not_found():
    resp = TEST_CLIENT.get(f'{ep.TEAMS_EP}/XYZ')
    assert resp.status_code == HTTPStatus.NOT_FOUND


def test_team_venue_resolves_through_the_api():
    team = TEST_CLIENT.get(f'{ep.TEAMS_EP}/BOS').get_json()[ep.TEAM_RESP]
    resp = TEST_CLIENT.get(f'{ep.VENUES_EP}/{team["venue_id"]}')
    assert resp.status_code == HTTPStatus.OK
    assert resp.get_json()[ep.VENUE_RESP]['name'] == 'TD Garden'
