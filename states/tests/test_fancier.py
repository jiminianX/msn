import os
from unittest.mock import patch

import pytest
from werkzeug.exceptions import NotFound

import server.endpoints as ep
import states.query as qry


@pytest.fixture
def client():
    return ep.app.test_client()


@pytest.fixture
def sample_states():
    return {
        "NY": {
            "name": "New York",
            "capital": "Albany",
            "population": 1000000,
        }
    }


def test_states_endpoint_with_fixture(client, sample_states):
    with patch(
        "server.endpoints.sqry.get_states",
        return_value=sample_states,
    ):
        response = client.get(ep.STATES_EP)

    assert response.status_code == 200
    assert response.get_json()[ep.STATES_RESP] == sample_states


def test_missing_state_raises_not_found():
    with patch(
        "server.endpoints.sqry.get_state",
        return_value=None,
    ):
        with pytest.raises(NotFound):
            ep.State().get("ZZ")


def test_database_unavailable_with_patch():
    with patch("states.query.is_db_up", return_value=False):
        assert qry.get_states() is None


@pytest.mark.skipif(
    os.getenv("RUN_DB_INTEGRATION") != "1",
    reason="Live MongoDB integration testing is not enabled",
)
def test_live_database_connection():
    assert qry.is_db_up()
