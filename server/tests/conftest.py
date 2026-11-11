"""
Keep the HTTP tests independent of a running database.

`is_db_up()` performs a real ping now, so on a machine with no mongod
every `/states` request answers 503 -- and once the venue loader reads
from the collection, so does every venue request. These tests are about
HTTP behaviour (status codes, response shape, query-parameter handling)
rather than about storage, so they are handed deterministic data.

Patching here rather than skipping keeps the suite meaningful on a
laptop with no database and on the CI runner alike, and keeps the
reason in one place instead of repeated across forty tests.

Storage has its own coverage, so nothing is lost:
  * `data/tests/test_db_connect.py` -- the probe and the CRUD helpers
  * `data/tests/test_load.py` -- the Mongo-backed loader
  * `data/tests/test_seed.py` -- the seeder
  * `states/tests/test_fancier.py` -- a real round trip, with
    RUN_DB_INTEGRATION=1

The unavailable paths are still tested in this package. The 503 tests
patch these same two seams in the opposite direction, which is exactly
why the seams are patched rather than the database faked wholesale.

Setting RUN_DB_INTEGRATION=1 makes the fixture step aside, so the same
suite runs end to end against a real seeded database. That flag is the
one `states/tests/test_fancier.py` already uses.
"""
import os

import pytest

import data.load as data_load
import states.query as sqry

INTEGRATION_ENV = 'RUN_DB_INTEGRATION'


@pytest.fixture(autouse=True)
def database_available(monkeypatch):
    """
    Report the database as up and serve venues from the CSV.

    `get_venue()` resolves `load_venues` through the module namespace
    at call time, so replacing that one attribute covers the single
    and the plural lookup together.
    """
    if os.getenv(INTEGRATION_ENV) == '1':
        return
    monkeypatch.setattr(sqry, 'is_db_up', lambda: True)
    monkeypatch.setattr(data_load, 'load_venues',
                        data_load.load_venues_from_csv)
