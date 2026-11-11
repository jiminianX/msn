#!/usr/bin/env python3
"""
Load the reference CSV files in this directory into MongoDB.

The CSVs stay the source of truth in version control; this script is
how that data reaches a database. The API reads from Mongo, so a fresh
checkout needs seeding once before the venue endpoints return anything:

    python -m data.seed

Seeding is idempotent. Each document is upserted on its natural key
rather than inserted, so running this twice leaves one copy of each
record instead of two. That matters because the obvious alternative --
drop the collection, then insert -- throws away any edit made through
the API, and because a half-finished run should be safe to repeat.
"""

import sys

import data.db_connect as dbc
import data.load as ld

VENUES_COLLECTION = 'venues'
COUNTRIES_COLLECTION = 'countries'
LEAGUES_COLLECTION = 'leagues'

# Each collection paired with the field that identifies a document, so
# re-seeding matches an existing record instead of adding another.
COLLECTION_KEYS = {
    VENUES_COLLECTION: ld.VENUE_ID,
    COUNTRIES_COLLECTION: ld.CODE,
    LEAGUES_COLLECTION: ld.CODE,
}


def seed_collection(collection, records, key):
    """
    Upsert every record into `collection`, matching on `key`.

    Args:
        collection (str): Collection name.
        records (iterable): Dicts to write.
        key (str): Field that identifies a document.

    Returns:
        int: How many records were written.

    Raises:
        ValueError: If a record is missing `key`, which would otherwise
            upsert against a filter of {key: None} and let every such
            record overwrite the same document.
    """
    handle = dbc.get_collection(collection)
    written = 0
    for record in records:
        if key not in record:
            raise ValueError(
                f'A {collection} record is missing {key!r}: {record!r}')
        handle.update_one({key: record[key]}, {'$set': record},
                          upsert=True)
        written += 1
    return written


def seed_all():
    """
    Seed every reference collection from its CSV.

    Returns:
        dict: Collection name mapped to the number of records written.
    """
    sources = {
        VENUES_COLLECTION: ld.load_venues_from_csv(),
        COUNTRIES_COLLECTION: ld.load_countries(),
        LEAGUES_COLLECTION: ld.load_leagues(),
    }
    counts = {}
    for collection, by_key in sources.items():
        counts[collection] = seed_collection(
            collection, by_key.values(), COLLECTION_KEYS[collection])
    return counts


def main():
    """
    Seed the database, reporting what was written.

    Exits non-zero when Mongo is unreachable, so `make seed` fails
    loudly rather than reporting success against no database.
    """
    if not dbc.is_db_up():
        print('MongoDB is not reachable -- start it and try again. '
              'On macOS: brew services start mongodb-community',
              file=sys.stderr)
        return 1
    for collection, count in seed_all().items():
        print(f'{collection}: {count} records')
    return 0


if __name__ == '__main__':
    sys.exit(main())
