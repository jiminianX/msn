"""
This is the file containing all of the endpoints for our flask app.
The endpoint called `endpoints` will return all available endpoints.
"""
from http import HTTPStatus

from flask import Flask, request
from flask_restx import Resource, Api  # , fields  # Namespace
from flask_cors import CORS

import werkzeug.exceptions as wz

import states.query as sqry
import data.load as data_load
from geo.distance import distance_miles
from geo.capacity import rank_venues_by_capacity
from geo.nearest import nearest_venue
from geo.road_trip import road_trip_miles

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
DISTANCE_EP = '/distance'
DISTANCE_RESP = 'Distance (miles)'
DISTANCE_PARAMS = ('lat1', 'lon1', 'lat2', 'lon2')
ROAD_TRIP_EP = '/road_trip'
ROAD_TRIP_RESP = 'Total distance (miles)'
ROAD_TRIP_VENUES = 'venues'
VENUES_EP = '/venues'
VENUES_RESP = 'Venues'
VENUE_RESP = 'Venue'
NEAREST_EP = f'{VENUES_EP}/nearest'
NEAREST_RESP = 'Nearest venue'
NEAREST_PARAMS = ('lat', 'lon')
BY_CAPACITY_EP = f'{VENUES_EP}/by_capacity'
BY_CAPACITY_RESP = 'Venues by capacity'
BY_CAPACITY_STATE = 'state'


def parse_float_args(names):
    """
    Read the named query parameters as floats, in the order given.

    Raises BadRequest (400) naming every missing parameter, or when a
    value cannot be parsed as a number. Range checks are left to the
    caller, since what counts as valid depends on the parameter.
    """
    missing = [name for name in names if name not in request.args]
    if missing:
        raise wz.BadRequest(
            f'Missing query parameter(s): {", ".join(missing)}.')
    try:
        return [float(request.args[name]) for name in names]
    except ValueError as err:
        raise wz.BadRequest(f'Query parameters must be numeric: {err}')


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


@api.route(DISTANCE_EP)
@api.doc(params={
    'lat1': 'Latitude of the first point, in decimal degrees (-90 to 90)',
    'lon1': 'Longitude of the first point, in decimal degrees (-180 to 180)',
    'lat2': 'Latitude of the second point, in decimal degrees (-90 to 90)',
    'lon2': 'Longitude of the second point, in decimal degrees (-180 to 180)',
})
class Distance(Resource):
    """
    Compute the great-circle distance between two coordinates.
    """
    @api.response(HTTPStatus.OK.value, 'Success')
    @api.response(HTTPStatus.BAD_REQUEST.value,
                  'Missing, non-numeric or out-of-range coordinate')
    def get(self):
        """
        Return the distance in miles between two latitude/longitude points.

        All four query parameters are required. Missing, non-numeric,
        non-finite or out-of-range values return 400.
        """
        coords = parse_float_args(DISTANCE_PARAMS)
        try:
            miles = distance_miles(*coords)
        except ValueError as err:
            raise wz.BadRequest(f'Invalid coordinates: {err}')
        return {DISTANCE_RESP: miles}


@api.route(ROAD_TRIP_EP)
class RoadTrip(Resource):
    """
    Total up the great-circle distance of a multi-venue trip.
    """
    @api.response(HTTPStatus.OK.value, 'Success')
    @api.response(HTTPStatus.BAD_REQUEST.value,
                  'Body is not JSON, or a venue has bad coordinates')
    def post(self):
        """
        Return the total mileage of a trip through venues, in order.

        Expects a JSON body of the form
        `{"venues": [{"latitude": 40.75, "longitude": -73.99}, ...]}`.
        A venue record from the venues data can be passed straight
        through, since it already carries both fields. An empty or
        single-venue list has zero travel distance.

        This is a POST rather than a GET because a trip has an
        unbounded number of stops, which does not fit in query
        parameters.
        """
        body = request.get_json(silent=True)
        if not isinstance(body, dict) or ROAD_TRIP_VENUES not in body:
            raise wz.BadRequest(
                f'JSON body must contain a {ROAD_TRIP_VENUES!r} key.')
        venues = body[ROAD_TRIP_VENUES]
        if not isinstance(venues, list):
            raise wz.BadRequest(
                f'{ROAD_TRIP_VENUES!r} must be a list of venues.')
        try:
            miles = road_trip_miles(venues)
        except ValueError as err:
            raise wz.BadRequest(f'Invalid venues: {err}')
        return {ROAD_TRIP_RESP: miles}


@api.route(VENUES_EP)
class Venues(Resource):
    """
    Return every NBA and MLS venue in the directory.
    """
    @api.response(HTTPStatus.OK.value, 'Success')
    def get(self):
        """
        Return all venues loaded from the CSV file, keyed on venue_id.
        """
        venues = data_load.load_venues()
        return {VENUES_RESP: venues}


@api.route(f'{VENUES_EP}/<venue_id>')
@api.doc(params={'venue_id': 'Venue identifier, e.g. MSG '
                             '(case-insensitive)'})
class Venue(Resource):
    """
    Look up a single venue by its identifier.
    """
    @api.response(HTTPStatus.OK.value, 'Success')
    @api.response(HTTPStatus.NOT_FOUND.value, 'Venue not found')
    def get(self, venue_id):
        """
        Return a single venue by its venue_id.

        Lookup is case-insensitive; unknown identifiers return 404.
        """
        venue = data_load.get_venue(venue_id)
        if venue is None:
            raise wz.NotFound(f'No venue found with id {venue_id!r}.')
        return {VENUE_RESP: venue}


@api.route(NEAREST_EP)
@api.doc(params={
    'lat': 'Latitude to search from, in decimal degrees (-90 to 90)',
    'lon': 'Longitude to search from, in decimal degrees (-180 to 180)',
})
class NearestVenue(Resource):
    """
    Find the venue closest to a coordinate.
    """
    @api.response(HTTPStatus.OK.value, 'Success')
    @api.response(HTTPStatus.BAD_REQUEST.value,
                  'Missing, non-numeric or out-of-range coordinate')
    def get(self):
        """
        Return the closest venue to lat/lon and its distance in miles.

        Both query parameters are required. Missing, non-numeric,
        non-finite or out-of-range values return 400.
        """
        lat, lon = parse_float_args(NEAREST_PARAMS)
        venues = list(data_load.load_venues().values())
        try:
            result = nearest_venue(lat, lon, venues)
        except ValueError as err:
            raise wz.BadRequest(f'Invalid coordinates: {err}')
        return {NEAREST_RESP: result}


@api.route(BY_CAPACITY_EP)
@api.doc(params={
    BY_CAPACITY_STATE: 'Optional two-letter state/province code, e.g. NY '
                       '(case-insensitive)',
})
class VenuesByCapacity(Resource):
    """
    Rank venues by seating capacity.
    """
    @api.response(HTTPStatus.OK.value, 'Success')
    def get(self):
        """
        Return venues sorted by capacity, largest first.

        Pass `state` to limit the ranking to one state or province;
        a code with no venues returns an empty list.
        """
        state = request.args.get(BY_CAPACITY_STATE)
        venues = list(data_load.load_venues().values())
        ranked = rank_venues_by_capacity(venues, state_code=state)
        return {BY_CAPACITY_RESP: ranked}
