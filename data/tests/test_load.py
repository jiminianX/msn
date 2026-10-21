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


def test_get_country():
    country = ld.get_country('us')
    assert country['name'] == 'United States'
    assert ld.get_country('US') == country


def test_get_country_not_found():
    assert ld.get_country('ZZ') is None
    assert ld.get_country(None) is None


def test_get_league():
    league = ld.get_league('nba')
    assert league['sport'] == 'Basketball'
    assert ld.get_league('NBA') == league


def test_get_league_not_found():
    assert ld.get_league('XFL') is None
    assert ld.get_league(None) is None
