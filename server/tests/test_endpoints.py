from http import HTTPStatus

import server.endpoints as ep

TEST_CLIENT = ep.app.test_client()


def test_hello():
    resp = TEST_CLIENT.get(ep.HELLO_EP)
    resp_json = resp.get_json()
    assert ep.HELLO_RESP in resp_json


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
