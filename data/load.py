#!/usr/bin/env python3
"""
Loaders for the reference CSV files that live in this directory.

Paths are built from this file's own location, so the loaders work no
matter which directory the caller runs from.
"""

import csv
import os

import data.db_connect as dbc
from geo.distance import distance_miles

DATA_DIR = os.path.dirname(__file__)
COUNTRIES_CSV = os.path.join(DATA_DIR, 'countries.csv')
LEAGUES_CSV = os.path.join(DATA_DIR, 'leagues.csv')
VENUES_CSV = os.path.join(DATA_DIR, 'venues.csv')

VENUES_COLLECTION = 'venues'

CODE = 'code'
VENUE_ID = 'venue_id'

VENUE_INT_FIELDS = ('capacity', 'opened_year')
VENUE_FLOAT_FIELDS = ('latitude', 'longitude')
VENUE_BOOL_FIELDS = ('indoor',)
TRUE_VALUES = ('true', 'yes', '1')
FALSE_VALUES = ('false', 'no', '0')

# Every field docs/DATA_MODEL.md lists for a venue. A create must supply
# all of them and nothing else.
VENUE_FIELDS = (
    VENUE_ID, 'name', 'city', 'state_code', 'country_code',
    'capacity', 'opened_year', 'latitude', 'longitude', 'indoor',
)
VENUE_TEXT_FIELDS = (VENUE_ID, 'name', 'city', 'state_code',
                     'country_code')

# Anything earlier than this is a typo rather than an opening year.
MIN_OPENED_YEAR = 1850


class VenueExists(Exception):
    """
    Raised when creating a venue whose venue_id is already taken.

    Deliberately not a ValueError: the payload is well formed, so the
    caller earns a 409 Conflict rather than a 400. That difference is
    actionable -- it says "change the id", not "fix the request".
    """


def load_csv(file_path):
    """
    Read a CSV file and return its rows as a list of dicts.

    Args:
        file_path (str): The path to the CSV file.

    Raises:
        FileNotFoundError: If file_path does not exist.
    """
    with open(file_path, mode='r') as csvfile:
        return list(csv.DictReader(csvfile))


def load_countries():
    """
    Return every country as a dict keyed on its two-letter code.
    """
    return {row[CODE]: row for row in load_csv(COUNTRIES_CSV)}


def load_leagues():
    """
    Return every league as a dict keyed on its code.
    """
    return {row[CODE]: row for row in load_csv(LEAGUES_CSV)}


def get_country(code):
    """
    Return one country's dict, looked up by its two-letter code
    (case-insensitive), or None if it isn't found.
    """
    if not isinstance(code, str):
        return None
    return load_countries().get(code.upper())


def get_league(code):
    """
    Return one league's dict, looked up by its code
    (case-insensitive), or None if it isn't found.
    """
    if not isinstance(code, str):
        return None
    return load_leagues().get(code.upper())


def typed_venue(row):
    """
    Return a copy of one venue row with its numeric and boolean fields
    converted from the text a CSV holds.

    Every CSV value arrives as a string, so an unconverted row serves
    `"capacity": "19812"` and `"indoor": "false"` over the API. The
    boolean is the dangerous one: a non-empty string is always truthy,
    in Python and in JavaScript alike, so `if venue['indoor']` is True
    for an outdoor stadium. Converting once here keeps every caller
    from having to coerce, and keeps them from forgetting to.

    Args:
        row (dict): One row as read from the venues CSV.

    Raises:
        ValueError: If a field is missing or cannot be converted,
            naming the venue and the field so a typo in the CSV points
            at itself instead of failing later inside a distance
            calculation.
    """
    venue = dict(row)
    venue_id = venue.get(VENUE_ID, '<unknown>')

    def convert(field, cast):
        try:
            return cast(venue[field])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(
                f'Venue {venue_id!r} has an invalid {field}: '
                f'{venue.get(field)!r}.') from exc

    for field in VENUE_INT_FIELDS:
        venue[field] = convert(field, int)
    for field in VENUE_FLOAT_FIELDS:
        venue[field] = convert(field, float)
    for field in VENUE_BOOL_FIELDS:
        raw = str(venue.get(field, '')).strip().lower()
        if raw in TRUE_VALUES:
            venue[field] = True
        elif raw in FALSE_VALUES:
            venue[field] = False
        else:
            raise ValueError(
                f'Venue {venue_id!r} has an invalid {field}: '
                f'{venue.get(field)!r}.')
    return venue


def load_venues_from_csv():
    """
    Return every venue from the CSV, keyed on its venue_id.

    This is the seed source: `data/seed.py` reads it to populate the
    venues collection. It is kept separate from `load_venues()` so the
    serving path and the seeding path cannot drift apart, and so the
    CSV stays readable without a database.
    """
    return {row[VENUE_ID]: typed_venue(row)
            for row in load_csv(VENUES_CSV)}


def load_venues():
    """
    Return every venue from the venues collection, keyed on venue_id.

    This reads from MongoDB, not from the CSV. The CSV remains the
    seed source in version control -- run `make seed` once on a fresh
    checkout -- and the database is what the API serves.

    No silent fallback to the CSV, deliberately: a fallback would make
    "Mongo is working" and "Mongo is broken" produce identical
    responses, so a passing request would prove nothing about the
    database and a real outage would look like a healthy API serving
    stale file data.

    Raises:
        dbc.DatabaseDown: when MongoDB is not reachable.
    """
    if not dbc.is_db_up():
        raise dbc.DatabaseDown(
            'MongoDB is not reachable; venue data is unavailable.')
    return dbc.read_dict(VENUES_COLLECTION, VENUE_ID)


def get_venue(venue_id):
    """
    Return one venue's dict, looked up by its venue_id
    (case-insensitive), or None if it isn't found.
    """
    if not isinstance(venue_id, str):
        return None
    return load_venues().get(venue_id.upper())


def validated_venue(payload):
    """
    Return a storage-ready venue record built from an API payload.

    Validation belongs here, at the boundary, rather than being left to
    the readers. One document with a latitude of 200 or a negative
    capacity makes `/venues/nearest` and `/venues/by_capacity` answer
    400 to every caller until somebody deletes it -- measured against a
    real database, not hypothetical. A write path that cannot produce
    such a document is worth more than four read paths that cope.

    Unknown fields are refused rather than ignored, so `capcity: 19812`
    fails loudly instead of silently storing a venue with no capacity
    and a stray key.

    venue_id is upper-cased because `get_venue()` upper-cases its
    lookup. Storing 'msg' would make `GET /venues/msg` a 404 for a
    venue that does exist, which is the kind of bug that takes an hour
    to find.

    Args:
        payload (dict): The venue as supplied by a client.

    Returns:
        dict: The record to store, with text trimmed, numbers and
            booleans converted, and venue_id upper-cased.

    Raises:
        ValueError: If a field is missing, unknown, empty, of the wrong
            type, or out of range.
    """
    if not isinstance(payload, dict):
        raise ValueError('a venue must be a JSON object')
    missing = [field for field in VENUE_FIELDS if field not in payload]
    if missing:
        raise ValueError(f'missing field(s): {", ".join(missing)}')
    unknown = sorted(set(payload) - set(VENUE_FIELDS))
    if unknown:
        raise ValueError(f'unknown field(s): {", ".join(unknown)}')

    # typed_venue does the conversions and already reports the field
    # and the offending value when one will not convert.
    venue = typed_venue(payload)

    for field in VENUE_TEXT_FIELDS:
        value = venue[field]
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f'{field} must be a non-empty string')
        venue[field] = value.strip()
    venue[VENUE_ID] = venue[VENUE_ID].upper()

    if venue['capacity'] < 0:
        raise ValueError('capacity cannot be negative')
    if venue['opened_year'] < MIN_OPENED_YEAR:
        raise ValueError(
            f'opened_year must be {MIN_OPENED_YEAR} or later')

    # Judge the coordinates with the geo package rather than restating
    # its ranges here, the same way nearest_venue validates its own
    # search point. Keeps one definition of a valid coordinate.
    distance_miles(venue['latitude'], venue['longitude'],
                   venue['latitude'], venue['longitude'])
    return venue


def create_venue(payload):
    """
    Validate a payload, store it as a new venue, and return the record.

    Args:
        payload (dict): The venue as supplied by a client.

    Returns:
        dict: The stored record. No `_id`: pymongo's insert_one adds
            one to the dict it is given, and an ObjectId is not JSON
            serializable, so the document handed to the driver is a
            copy and the caller gets the clean record back.

    Raises:
        ValueError: If the payload is not a valid venue.
        VenueExists: If a venue with that venue_id is already stored.
        dbc.DatabaseDown: If MongoDB is not reachable.
    """
    record = validated_venue(payload)
    if not dbc.is_db_up():
        raise dbc.DatabaseDown(
            'MongoDB is not reachable; the venue was not created.')
    if dbc.read_one(VENUES_COLLECTION, {VENUE_ID: record[VENUE_ID]}):
        raise VenueExists(
            f'a venue with id {record[VENUE_ID]!r} already exists')
    dbc.create(VENUES_COLLECTION, dict(record))
    return record
