"""
Tests for the CSV-to-MongoDB seeder.

These run with no mongod. The fake collection below stores what it is
given rather than returning a canned answer, which is what lets the
idempotency claim actually be tested: seed twice, assert one copy.
"""
import pytest

import data.db_connect as dbc
import data.seed as seed


class StoringCollection:
    """
    An in-memory stand-in for a Mongo collection.

    Only `update_one` with upsert is implemented, because that is all
    the seeder uses. Documents are kept in a dict keyed on the filter,
    so a second upsert against the same key replaces rather than adds
    -- the same thing a real unique upsert does.
    """
    def __init__(self, name):
        self.name = name
        self.docs = {}
        self.upserts = 0

    def update_one(self, filt, update, upsert=False):
        assert upsert, 'the seeder must upsert, not insert'
        key = tuple(sorted(filt.items()))
        self.docs[key] = dict(update['$set'])
        self.upserts += 1


class StoringDB:
    def __init__(self):
        self.collections = {}

    def __getitem__(self, name):
        return self.collections.setdefault(name, StoringCollection(name))


class StoringClient:
    def __init__(self, *args, **kwargs):
        self.dbs = {}

    def __getitem__(self, name):
        return self.dbs.setdefault(name, StoringDB())


@pytest.fixture
def store(monkeypatch):
    """
    Point the data layer at the in-memory store and hand it back.
    """
    monkeypatch.delenv('CLOUD_MONGO', raising=False)
    monkeypatch.setattr(dbc, 'client', None)
    client = StoringClient()
    monkeypatch.setattr(dbc.pm, 'MongoClient',
                        lambda *a, **kw: client)
    return client


def collection_of(store, name):
    return store[dbc.SE_DB].collections[name]


def test_seed_all_writes_every_collection(store):
    counts = seed.seed_all()
    assert set(counts) == {
        seed.VENUES_COLLECTION,
        seed.COUNTRIES_COLLECTION,
        seed.LEAGUES_COLLECTION,
    }
    assert counts[seed.VENUES_COLLECTION] == 16
    assert all(count > 0 for count in counts.values())


def test_seed_writes_the_venue_documents(store):
    seed.seed_all()
    venues = collection_of(store, seed.VENUES_COLLECTION)
    assert len(venues.docs) == 16
    msg = venues.docs[(('venue_id', 'MSG'),)]
    assert msg['name'] == 'Madison Square Garden'
    # Types survive the trip, so documents land as numbers and
    # booleans rather than as the CSV's text.
    assert msg['capacity'] == 19812
    assert msg['indoor'] is True


def test_seeding_twice_leaves_one_copy(store):
    seed.seed_all()
    seed.seed_all()
    venues = collection_of(store, seed.VENUES_COLLECTION)
    assert len(venues.docs) == 16
    assert venues.upserts == 32


def test_seed_collection_rejects_a_record_without_its_key(store):
    """
    An upsert filtered on a missing key becomes {key: None}, which
    makes every keyless record overwrite the same document instead of
    failing. Better to refuse.
    """
    with pytest.raises(ValueError) as err:
        seed.seed_collection('venues', [{'name': 'No Id'}], 'venue_id')
    assert 'venue_id' in str(err.value)


def test_main_fails_when_the_database_is_down(monkeypatch, capsys):
    monkeypatch.setattr(seed.dbc, 'is_db_up', lambda: False)
    assert seed.main() == 1
    assert 'not reachable' in capsys.readouterr().err


def test_main_reports_what_it_wrote(store, monkeypatch, capsys):
    monkeypatch.setattr(seed.dbc, 'is_db_up', lambda: True)
    assert seed.main() == 0
    out = capsys.readouterr().out
    assert 'venues: 16 records' in out
