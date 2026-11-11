#!/usr/bin/env python3
"""
Loaders for the reference CSV files that live in this directory.

Paths are built from this file's own location, so the loaders work no
matter which directory the caller runs from.
"""

import csv
import os

import data.db_connect as dbc

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
