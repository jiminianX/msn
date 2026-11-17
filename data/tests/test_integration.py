"""
End-to-end tests against a real MongoDB.

Skipped unless RUN_DB_INTEGRATION=1, the same flag
`states/tests/test_fancier.py` uses, so `make all_tests` stays green
on a machine with no database and in CI.

Everything else in the suite substitutes the storage layer at a seam.
These do not: they write to the real collection and read it back,
which is the only way to catch a mismatch between the fakes and the
driver -- a filter that works on a dict but not in BSON, say.

Each test removes what it created, in a fixture so a failed assertion
still cleans up. That is only possible because delete now exists; a
create-only API would leave a document behind on every run.
"""
import os

import pytest

import data.db_connect as dbc
import data.load as ld

pytestmark = pytest.mark.skipif(
    os.getenv('RUN_DB_INTEGRATION') != '1',
    reason='Live MongoDB integration testing is not enabled',
)

# Deliberately not a real venue id, so a stray document from a crashed
# run is obvious and cannot be mistaken for seeded data.
TEST_ID = 'ZZTESTVENUE'

A_VENUE = {
    'venue_id': TEST_ID,
    'name': 'Integration Test Arena',
    'city': 'Testville',
    'state_code': 'NY',
    'country_code': 'US',
    'capacity': 1234,
    'opened_year': 2020,
    'latitude': 40.0,
    'longitude': -74.0,
    'indoor': True,
}


@pytest.fixture(autouse=True)
def remove_the_test_venue():
    """
    Clear the test id before and after, so a crashed earlier run
    cannot make the next one fail on a duplicate.
    """
    ld.delete_venue(TEST_ID)
    yield
    ld.delete_venue(TEST_ID)


def test_the_database_is_reachable():
    assert dbc.is_db_up() is True


def test_the_collection_is_seeded():
    """
    If this fails, run `make seed`. The other tests assume the seeded
    venues are present.
    """
    venues = ld.load_venues()
    assert len(venues) >= 16
    assert 'MSG' in venues


def test_create_read_delete_round_trip():
    record = ld.create_venue(dict(A_VENUE))
    assert record['venue_id'] == TEST_ID

    # Read it back through the normal read path, not the return value.
    fetched = ld.get_venue(TEST_ID)
    assert fetched is not None
    assert fetched['name'] == 'Integration Test Arena'

    # BSON round trip: these would come back as strings if the write
    # path ever stopped converting them.
    assert fetched['capacity'] == 1234
    assert isinstance(fetched['capacity'], int)
    assert fetched['indoor'] is True
    assert fetched['latitude'] == 40.0
    assert dbc.MONGO_ID not in fetched

    assert ld.delete_venue(TEST_ID) is True
    assert ld.get_venue(TEST_ID) is None


def test_deleting_an_absent_venue_reports_false():
    assert ld.delete_venue(TEST_ID) is False


def test_delete_is_case_insensitive_in_the_real_database():
    ld.create_venue(dict(A_VENUE))
    assert ld.delete_venue(TEST_ID.lower()) is True
    assert ld.get_venue(TEST_ID) is None


def test_delete_leaves_the_seeded_venues_alone():
    before = set(ld.load_venues())
    ld.create_venue(dict(A_VENUE))
    ld.delete_venue(TEST_ID)
    assert set(ld.load_venues()) == before
