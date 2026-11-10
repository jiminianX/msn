# Pro Sports Venue Directory

[![CI](https://github.com/jiminianX/msn/actions/workflows/main.yml/badge.svg)](https://github.com/jiminianX/msn/actions/workflows/main.yml)

The Pro Sports Venue Directory is a REST API built with Flask that organizes NBA and MLS teams and their home venues by country, state/province, city, venue, and team. In addition to basic CRUD operations, the project will support geographic queries such as finding the nearest venue to a coordinate, calculating the distance between teams' arenas or stadiums, and identifying cities with teams in both leagues. The API focuses on venue and team information, not live scores or game statistics.

## Current Status

The project is currently in early development. The following endpoints are implemented:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/hello` | Returns a basic greeting to verify that the API is running. |
| GET | `/endpoints` | Lists available API endpoints. |
| GET | `/states` | Returns three hardcoded states (503 if the database is down). |
| GET | `/states/<abbrev>` | Returns one state by its two-letter abbreviation. |
| GET | `/countries` | Lists the supported countries. |
| GET | `/countries/<code>` | Returns one country by its two-letter code. |
| GET | `/leagues` | Lists the supported leagues. |
| GET | `/leagues/<code>` | Returns one league by its code, e.g. `NBA`. |
| GET | `/venues` | Lists every NBA and MLS venue, keyed on `venue_id`. |
| GET | `/venues/<venue_id>` | Returns one venue, e.g. `/venues/MSG`. |
| GET | `/venues/nearest?lat=&lon=` | Returns the venue closest to a coordinate and its distance in miles. |
| GET | `/venues/by_capacity?state=` | Ranks venues by capacity, largest first; `state` is optional. |
| GET | `/distance?lat1=&lon1=&lat2=&lon2=` | Returns the great-circle distance in miles between two points. |
| POST | `/road_trip` | Totals the mileage of a trip through a JSON list of venues, in order. |
| GET | `/swagger.json` | Returns the API's Swagger specification. |

Path lookups are case-insensitive and return 404 for unknown codes. Missing or invalid query parameters return 400.

**Current limitations:**
- State data currently consists of three hardcoded entries instead of records from MongoDB.
- Country, league, and venue data is read from CSV files in `data/` rather than MongoDB.

## Prerequisites

Before setting up the project, ensure you have:

- Python 3.9 or newer
- Git
- Make
- MongoDB configured to run on port `27017`

## Development Setup

Clone the repository and navigate into the project directory:

```bash
git clone https://github.com/jiminianX/msn.git
cd msn
```

Create a Python virtual environment:

```bash
python3 -m venv geodata2026-venv
```

Activate the environment:

```bash
source geodata2026-venv/bin/activate
```

Install the project's development dependencies:

```bash
make dev_env
```

Set the Python module search path:

```bash
export PYTHONPATH=$(pwd)
```

**Important:** The `PYTHONPATH` configuration is required so that the development server and tests can import the project's packages by their top-level names. Without it, imports may fail.

These commands assume a Bash-compatible shell.

## Running the Application

Start the local Flask development server:

```bash
./local.sh
```

The application will be available at:

http://127.0.0.1:8000

The Swagger UI is accessible at the root URL.

## Running Tests

Run the complete project test suite:

```bash
make all_tests
```

This command runs flake8 linting and pytest tests for the project's packages.

## Planned Features

The project aims to support:

- CRUD endpoints for countries, states/provinces, cities, venues, teams, and leagues.
- Finding the nearest NBA or MLS venue to a geographic coordinate.
- Calculating distances between teams' home venues.
- Calculating total travel distances for multi-game road trips.
- Identifying cities with both NBA and MLS teams.
- Ranking venues by seating capacity.

These features are planned and are not yet available through the API.

## Team

- Joseph Jiminian
- Jason Legarda
- Angel Perez