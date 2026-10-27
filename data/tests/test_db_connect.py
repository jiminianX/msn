"""
Tests for the Mongo access layer.

Every test here runs with no mongod: pymongo's MongoClient is swapped for
a fake, so CI never needs a database.
"""
import pytest

import data.db_connect as dbc


class FakeCollection:
    def __init__(self, name):
        self.name = name


class FakeDB:
    def __init__(self, name):
        self.name = name

    def __getitem__(self, collection):
        return FakeCollection(collection)


class FakeClient:
    def __init__(self, *args, **kwargs):
        self.args = args

    def __getitem__(self, db):
        return FakeDB(db)


@pytest.fixture(autouse=True)
def reset_client():
    """
    connect_db() caches into a module global, so reset it around every
    test and test ordering cannot matter.
    """
    saved = dbc.client
    dbc.client = None
    yield
    dbc.client = saved


@pytest.fixture
def fake_mongo(monkeypatch):
    monkeypatch.delenv('CLOUD_MONGO', raising=False)
    monkeypatch.setattr(dbc.pm, 'MongoClient', FakeClient)


def test_convert_mongo_id():
    doc = {dbc.MONGO_ID: 123, 'name': 'Yankee Stadium'}
    dbc.convert_mongo_id(doc)
    assert doc[dbc.MONGO_ID] == '123'
    assert doc['name'] == 'Yankee Stadium'


def test_convert_mongo_id_absent():
    """
    No _id means no change -- pinned so nobody 'simplifies' this into a
    function that inserts a key that was never there.
    """
    doc = {'name': 'Yankee Stadium'}
    dbc.convert_mongo_id(doc)
    assert doc == {'name': 'Yankee Stadium'}


def test_connect_db_local(fake_mongo):
    assert isinstance(dbc.connect_db(), FakeClient)


def test_connect_db_caches(fake_mongo):
    assert dbc.connect_db() is dbc.connect_db()


def test_connect_db_cloud_needs_password(monkeypatch):
    monkeypatch.setenv('CLOUD_MONGO', dbc.CLOUD)
    monkeypatch.delenv('MONGO_PASSWD', raising=False)
    monkeypatch.setattr(dbc.pm, 'MongoClient', FakeClient)
    with pytest.raises(ValueError):
        dbc.connect_db()


def test_get_collection_connects_on_demand(fake_mongo):
    """
    The regression test: with client still None, the old
    client[db][collection] raised TypeError instead of connecting.
    """
    assert dbc.client is None
    collection = dbc.get_collection('venues')
    assert collection.name == 'venues'
    assert dbc.client is not None


def test_get_collection_uses_default_db(fake_mongo):
    assert dbc.connect_db()[dbc.SE_DB].name == dbc.SE_DB
