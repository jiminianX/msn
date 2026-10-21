from http import HTTPStatus

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
