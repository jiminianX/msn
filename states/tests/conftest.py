"""
Keep the states tests independent of a running database.

`is_db_up()` performs a real ping now, so `get_states()` returns None on
any machine without a mongod and the tests about query logic -- lookup,
case-insensitivity, the non-string guard -- would all fail for a reason
that has nothing to do with what they check.

The fixture steps aside when RUN_DB_INTEGRATION=1, which is the flag
`test_fancier.py::test_live_database_connection` is already gated on.
Without that exemption the autouse patch would force `is_db_up()` to
True and the one test whose whole purpose is a real round trip would
pass against no database at all.

The db-down tests patch the same seam to False in their own bodies,
which runs after this fixture and therefore wins.
"""
import os

import pytest

import states.query as qry

INTEGRATION_ENV = 'RUN_DB_INTEGRATION'


@pytest.fixture(autouse=True)
def database_available(monkeypatch):
    if os.getenv(INTEGRATION_ENV) == '1':
        return
    monkeypatch.setattr(qry, 'is_db_up', lambda: True)
