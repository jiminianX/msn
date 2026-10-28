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
