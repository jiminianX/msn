#!/usr/bin/env python3
"""
Loaders for the reference CSV files that live in this directory.

Paths are built from this file's own location, so the loaders work no
matter which directory the caller runs from.
"""

import csv
import os

DATA_DIR = os.path.dirname(__file__)
COUNTRIES_CSV = os.path.join(DATA_DIR, 'countries.csv')
LEAGUES_CSV = os.path.join(DATA_DIR, 'leagues.csv')

CODE = 'code'


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
