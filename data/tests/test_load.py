import pytest

import data.load as ld


def test_load_countries():
    countries = ld.load_countries()
    assert 'US' in countries
    assert 'CA' in countries
    assert countries['CA']['name'] == 'Canada'


def test_load_leagues():
    leagues = ld.load_leagues()
    assert 'NBA' in leagues
    assert 'MLS' in leagues
    assert leagues['MLS']['sport'] == 'Soccer'


def test_load_csv_missing_file():
    with pytest.raises(FileNotFoundError):
        ld.load_csv('no/such/file.csv')
