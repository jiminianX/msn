"""
All interaction with MongoDB should be through this file!
We may be required to use a new database at any point.
"""
import functools
import os

import pymongo as pm

LOCAL = "0"
CLOUD = "1"

SE_DB = 'seDB'

client = None

MONGO_ID = '_id'

# pymongo connects lazily and its server-selection timeout defaults to
# 30 seconds, so MongoClient() succeeds against a dead database and the
# wait only arrives on the first real operation. Two seconds is long
# enough for a local mongod to answer and short enough that a request
# fails fast instead of appearing to hang.
SERVER_SELECTION_TIMEOUT_MS = 2000

# A liveness probe should give up sooner still -- it is answering "is
# the database there", and an endpoint calls it before doing any work.
PING_TIMEOUT_MS = 500


def connect_db():
    """
    This provides a uniform way to connect to the DB across all uses.
    Returns a mongo client object... maybe we shouldn't?
    Also set global client variable.
    We should probably either return a client OR set a
    client global.
    """
    global client
    if client is None:  # not connected yet!
        print('Setting client because it is None.')
        if os.environ.get('CLOUD_MONGO', LOCAL) == CLOUD:
            password = os.environ.get('MONGO_PASSWD')
            if not password:
                raise ValueError('You must set your password '
                                 + 'to use Mongo in the cloud.')
            print('Connecting to Mongo in the cloud.')
            client = pm.MongoClient(
                f'mongodb+srv://gcallah:{password}'
                + '@koukoumongo1.yud9b.mongodb.net/'
                + '?retryWrites=true&w=majority',
                serverSelectionTimeoutMS=SERVER_SELECTION_TIMEOUT_MS)
        else:
            print("Connecting to Mongo locally.")
            client = pm.MongoClient(
                serverSelectionTimeoutMS=SERVER_SELECTION_TIMEOUT_MS)
    return client


def needs_connection(fn):
    """
    Guarantee a live Mongo client before `fn` runs.

    Every database function in this module reads the module-level
    `client`, which starts out as None. Opening each body with its own
    connect_db() call means eight separate chances to forget one, and a
    forgotten one fails as `TypeError: 'NoneType' object is not
    subscriptable` -- an error that says nothing about connections.
    Stating the requirement once here and applying it as
    @needs_connection keeps it attached to each function instead of
    resting on everyone remembering a convention.

    connect_db() is idempotent -- it returns the cached client once one
    exists -- so a decorated function calling another decorated
    function costs one extra comparison, not a second connection.

    functools.wraps keeps the wrapped function's name, signature and
    docstring, so the decorator stays invisible to anything that
    introspects this module.
    """
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        connect_db()
        return fn(*args, **kwargs)
    return wrapper


def is_db_up():
    """
    Return True when MongoDB answers a ping, False otherwise.

    This used to `return True` unconditionally, which made every caller
    believe a database was present even with nothing installed. The
    check has to be an actual round trip: pymongo connects lazily, so
    `MongoClient()` succeeds against a dead server and `client` being
    non-None proves only that an object exists.

    `ping` is the cheapest command that proves the server is reachable
    and answering. It runs against the `admin` database, which needs no
    application data and exists on every deployment.

    Never raises. A caller asking whether the database is up wants an
    answer, not an exception to handle -- `states/query.py` and the
    endpoints both branch on this, so an exception here would turn a
    known-unavailable database into a 500.
    """
    try:
        connect_db().admin.command(
            'ping', maxTimeMS=PING_TIMEOUT_MS)
    except pm.errors.PyMongoError as err:
        print(f'MongoDB is not reachable: {err}')
        return False
    return True


def convert_mongo_id(doc: dict):
    if MONGO_ID in doc:
        # Convert mongo ID to a string so it works as JSON
        doc[MONGO_ID] = str(doc[MONGO_ID])


@needs_connection
def get_collection(collection, db=SE_DB):
    """
    Return a handle to one collection.

    @needs_connection has already guaranteed `client` is live by the
    time this body runs, which is why it can index the global directly.
    """
    return client[db][collection]


@needs_connection
def create(collection, doc, db=SE_DB):
    """
    Insert a single doc into collection.
    """
    print(f'{db=}')
    return get_collection(collection, db).insert_one(doc)


@needs_connection
def read_one(collection, filt, db=SE_DB):
    """
    Find with a filter and return on the first doc found.
    Return None if not found.
    """
    for doc in get_collection(collection, db).find(filt):
        convert_mongo_id(doc)
        return doc


@needs_connection
def delete(collection: str, filt: dict, db=SE_DB):
    """
    Find with a filter and return on the first doc found.
    """
    print(f'{filt=}')
    del_result = get_collection(collection, db).delete_one(filt)
    return del_result.deleted_count


@needs_connection
def update(collection, filters, update_dict, db=SE_DB):
    return get_collection(collection, db).update_one(
        filters, {'$set': update_dict})


@needs_connection
def read(collection, db=SE_DB, no_id=True) -> list:
    """
    Returns a list from the db.
    """
    ret = []
    for doc in get_collection(collection, db).find():
        if no_id:
            del doc[MONGO_ID]
        else:
            convert_mongo_id(doc)
        ret.append(doc)
    return ret


@needs_connection
def read_dict(collection, key, db=SE_DB, no_id=True) -> dict:
    recs = read(collection, db=db, no_id=no_id)
    recs_as_dict = {}
    for rec in recs:
        recs_as_dict[rec[key]] = rec
    return recs_as_dict


@needs_connection
def fetch_all_as_dict(key, collection, db=SE_DB):
    ret = {}
    for doc in get_collection(collection, db).find():
        del doc[MONGO_ID]
        ret[doc[key]] = doc
    return ret
