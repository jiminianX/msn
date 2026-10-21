"""
This is the file containing all of the endpoints for our flask app.
The endpoint called `endpoints` will return all available endpoints.
"""
from http import HTTPStatus

from flask import Flask  # , request
from flask_restx import Resource, Api  # , fields  # Namespace
from flask_cors import CORS

import werkzeug.exceptions as wz

import states.query as sqry
import data.load as data_load

app = Flask(__name__)
CORS(app)
api = Api(app)

ENDPOINT_EP = '/endpoints'
ENDPOINT_RESP = 'Available endpoints'
HELLO_EP = '/hello'
HELLO_RESP = 'hello'
STATES_EP = '/states'
STATES_RESP = 'States:'
STATE_RESP = 'State'
COUNTRIES_EP = '/countries'
COUNTRIES_RESP = 'Countries'
COUNTRY_RESP = 'Country'
LEAGUES_EP = '/leagues'
LEAGUES_RESP = 'Leagues'
LEAGUE_RESP = 'League'


@api.route(HELLO_EP)
class HelloWorld(Resource):
    """
    The purpose of the HelloWorld class is to have a simple test to see if the
    app is working at all.
    """
    def get(self):
        """
        A trivial endpoint to see if the server is running.
        """
        return {HELLO_RESP: 'world'}


@api.route(ENDPOINT_EP)
class Endpoints(Resource):
    """
    This class will serve as live, fetchable documentation of what endpoints
    are available in the system.
    """
    def get(self):
        """
        The `get()` method will return a sorted list of available endpoints.
        """
        endpoints = sorted(rule.rule for rule in api.app.url_map.iter_rules())
        return {ENDPOINT_RESP: endpoints}


@api.route(STATES_EP)
class States(Resource):
    """
    The get method will return a list of all states in the database.
    """
    @api.response(HTTPStatus.OK.value, 'Success')
    @api.response(HTTPStatus.SERVICE_UNAVAILABLE.value, 'Service Unavailable')
    def get(self):
        """
        The get method will return a list of all states in the database.
        """
        states = sqry.get_states()
        if states is None:
            raise wz.ServiceUnavailable('Database may be down.')
        return {STATES_RESP: states}


@api.route(f'{STATES_EP}/<abbrev>')
@api.doc(params={'abbrev': 'Two-letter state abbreviation, e.g. AL '
                           '(case-insensitive)'})
class State(Resource):
    """
    Look up a single state by its abbreviation.
    """
    @api.response(HTTPStatus.OK.value, 'Success')
    @api.response(HTTPStatus.NOT_FOUND.value, 'State not found')
    def get(self, abbrev):
        """
        Return a single state by its two-letter abbreviation.

        The response holds the state's name, capital, population and area.
        Lookup is case-insensitive; unknown abbreviations return 404.
        """
        state = sqry.get_state(abbrev)
        if state is None:
            raise wz.NotFound(f'No state found with abbreviation '
                              f'{abbrev!r}.')
        return {STATE_RESP: state}


@api.route(COUNTRIES_EP)
class Countries(Resource):
    """
    Return the countries supported by the sports venue directory.
    """
    @api.response(HTTPStatus.OK.value, 'Success')
    def get(self):
        """
        Return country information loaded from the CSV file.
        """
        countries = data_load.load_countries()
        return {COUNTRIES_RESP: countries}


@api.route(LEAGUES_EP)
class Leagues(Resource):
    """
    Return the sports leagues supported by the directory.
    """
    @api.response(HTTPStatus.OK.value, 'Success')
    def get(self):
        """
        Return league information loaded from the CSV file.
        """
        leagues = data_load.load_leagues()
        return {LEAGUES_RESP: leagues}


@api.route(f'{COUNTRIES_EP}/<code>')
@api.doc(params={'code': 'Two-letter country code, e.g. US '
                         '(case-insensitive)'})
class Country(Resource):
    """
    Look up a single country by its code.
    """
    @api.response(HTTPStatus.OK.value, 'Success')
    @api.response(HTTPStatus.NOT_FOUND.value, 'Country not found')
    def get(self, code):
        """
        Return a single country by its two-letter code.

        Lookup is case-insensitive; unknown codes return 404.
        """
        country = data_load.get_country(code)
        if country is None:
            raise wz.NotFound(f'No country found with code {code!r}.')
        return {COUNTRY_RESP: country}


@api.route(f'{LEAGUES_EP}/<code>')
@api.doc(params={'code': 'League code, e.g. NBA (case-insensitive)'})
class League(Resource):
    """
    Look up a single league by its code.
    """
    @api.response(HTTPStatus.OK.value, 'Success')
    @api.response(HTTPStatus.NOT_FOUND.value, 'League not found')
    def get(self, code):
        """
        Return a single league by its code.

        Lookup is case-insensitive; unknown codes return 404.
        """
        league = data_load.get_league(code)
        if league is None:
            raise wz.NotFound(f'No league found with code {code!r}.')
        return {LEAGUE_RESP: league}
