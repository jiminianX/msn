from http import HTTPStatus

import pytest

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
