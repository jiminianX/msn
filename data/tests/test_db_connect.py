"""
Tests for the Mongo access layer.

Every test here runs with no mongod: pymongo's MongoClient is swapped for
a fake, so CI never needs a database.
"""
import pytest

import pymongo as pm

import data.db_connect as dbc


class FakeDeleteResult:
    def __init__(self, deleted_count):
        self.deleted_count = deleted_count


class FakeCollection:
    def __init__(self, name):
        self.name = name

    def insert_one(self, doc):
        return doc

    def find(self, filt=None):
        return [{dbc.MONGO_ID: 1, 'venue_id': 'MSG'}]

    def delete_one(self, filt):
        return FakeDeleteResult(1)

    def update_one(self, filt, update):
        return update


class FakeDB:
    def __init__(self, name):
        self.name = name

    def __getitem__(self, collection):
        return FakeCollection(collection)


class FakeClient:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.admin = FakeAdmin()

    def __getitem__(self, db):
        return FakeDB(db)


class FakeAdmin:
    """
    Stands in for client.admin, which is where `ping` runs.
    """
    def __init__(self):
        self.commands = []

    def command(self, name, **kwargs):
        self.commands.append((name, kwargs))
        return {'ok': 1}


class UnreachableAdmin:
    def command(self, name, **kwargs):
        raise pm.errors.ServerSelectionTimeoutError(
            'localhost:27017: [Errno 61] Connection refused')


class UnreachableClient(FakeClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.admin = UnreachableAdmin()


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


# Every public function in db_connect that touches the database. A new
# one added without @needs_connection should fail the test below.
DB_FUNCTIONS = (
    'get_collection',
    'create',
    'read_one',
    'delete',
    'update',
    'read',
    'read_dict',
    'fetch_all_as_dict',
)


@pytest.mark.parametrize('name', DB_FUNCTIONS)
def test_every_db_function_is_decorated(name):
    """
    functools.wraps sets __wrapped__, so this is what it looks like
    from the outside when @needs_connection is in place. This is the
    test that keeps the guarantee true for functions written later.
    """
    assert hasattr(getattr(dbc, name), '__wrapped__')


def test_needs_connection_connects_before_the_body_runs():
    seen = []

    @dbc.needs_connection
    def peek():
        seen.append(dbc.client)

    assert dbc.client is None
    peek()
    assert seen == [dbc.client]
    assert dbc.client is not None


def test_needs_connection_reuses_one_client(fake_mongo):
    @dbc.needs_connection
    def peek():
        return dbc.client

    assert peek() is peek()


def test_needs_connection_passes_args_and_returns(fake_mongo):
    @dbc.needs_connection
    def add(first, second, third=0):
        return first + second + third

    assert add(1, 2, third=3) == 6


def test_needs_connection_preserves_identity():
    """
    Without functools.wraps every decorated function would report
    itself as 'wrapper' with no docstring, which breaks introspection
    and any documentation built from it.
    """
    assert dbc.create.__name__ == 'create'
    assert 'Insert a single doc' in dbc.create.__doc__


def test_needs_connection_propagates_errors(monkeypatch):
    monkeypatch.delenv('CLOUD_MONGO', raising=False)
    monkeypatch.setattr(dbc.pm, 'MongoClient', FakeClient)

    @dbc.needs_connection
    def boom():
        raise KeyError('from the body')

    with pytest.raises(KeyError):
        boom()


def test_crud_connects_with_no_client(fake_mongo):
    """
    End to end: with client still None, a CRUD call now opens the
    connection itself instead of raising TypeError on a None subscript.
    """
    assert dbc.client is None
    docs = dbc.read('venues')
    assert docs == [{'venue_id': 'MSG'}]
    assert dbc.client is not None


def test_crud_helpers_reach_the_collection(fake_mongo):
    assert dbc.create('venues', {'venue_id': 'MSG'}) == {'venue_id': 'MSG'}
    assert dbc.read_one('venues', {}) == {dbc.MONGO_ID: '1',
                                          'venue_id': 'MSG'}
    assert dbc.delete('venues', {}) == 1
    assert dbc.update('venues', {}, {'city': 'New York'}) == {
        '$set': {'city': 'New York'}}
    assert dbc.read_dict('venues', 'venue_id') == {
        'MSG': {'venue_id': 'MSG'}}
    assert dbc.fetch_all_as_dict('venue_id', 'venues') == {
        'MSG': {'venue_id': 'MSG'}}


def test_is_db_up_pings_the_server(fake_mongo):
    assert dbc.is_db_up() is True
    # The point of the rewrite: it is a real round trip, not a
    # hardcoded True. Assert the command was actually issued.
    assert dbc.client.admin.commands == [
        ('ping', {'maxTimeMS': dbc.PING_TIMEOUT_MS})]


def test_is_db_up_is_false_when_unreachable(monkeypatch):
    monkeypatch.delenv('CLOUD_MONGO', raising=False)
    monkeypatch.setattr(dbc.pm, 'MongoClient', UnreachableClient)
    assert dbc.is_db_up() is False


def test_is_db_up_does_not_raise_when_unreachable(monkeypatch):
    """
    Callers branch on this rather than catching -- states/query.py and
    the endpoints both do -- so an exception here would turn a
    known-unavailable database into a 500 instead of a 503.
    """
    monkeypatch.delenv('CLOUD_MONGO', raising=False)
    monkeypatch.setattr(dbc.pm, 'MongoClient', UnreachableClient)
    assert dbc.is_db_up() is False
    assert dbc.is_db_up() is False


def test_connect_db_sets_an_explicit_timeout(fake_mongo):
    """
    pymongo defaults serverSelectionTimeoutMS to 30 seconds, so
    without this a dead database makes every request hang for half a
    minute before failing.
    """
    created = dbc.connect_db()
    assert created.kwargs['serverSelectionTimeoutMS'] == (
        dbc.SERVER_SELECTION_TIMEOUT_MS)
    assert dbc.SERVER_SELECTION_TIMEOUT_MS < 30000
