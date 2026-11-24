# Pro Sports Venue Directory

[![CI](https://github.com/jiminianX/msn/actions/workflows/main.yml/badge.svg)](https://github.com/jiminianX/msn/actions/workflows/main.yml)

The Pro Sports Venue Directory is a REST API built with Flask that organizes NBA and MLS teams and their home venues by country, state/province, city, venue, and team. In addition to basic CRUD operations, the project will support geographic queries such as finding the nearest venue to a coordinate, calculating the distance between teams' arenas or stadiums, and identifying cities with teams in both leagues. The API focuses on venue and team information, not live scores or game statistics.

## Current Status

The venue endpoints are complete and backed by MongoDB; teams are readable from `data/teams.csv`; cities and the remaining collections are still to come. The following endpoints are implemented:

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
| GET | `/venues?country=&state=` | Lists every NBA and MLS venue, keyed on `venue_id`. Both filters are optional, case-insensitive, and combine; `country` is a country code, `state` a state/province code. An unknown code returns an empty result rather than 404. Read from MongoDB; 503 if the database is unreachable. |
| POST | `/venues` | Creates a venue from a JSON body and stores it in MongoDB. All ten fields in `docs/DATA_MODEL.md` are required and no others are accepted; `venue_id` is stored upper-cased. Returns 201 with a `Location` header, 400 for an invalid body, 409 if the `venue_id` is taken, 503 if the database is unreachable. |
| GET | `/venues/<venue_id>` | Returns one venue, e.g. `/venues/MSG`. Read from MongoDB; 503 if the database is unreachable. |
| DELETE | `/venues/<venue_id>` | Deletes one venue from MongoDB, e.g. `/venues/MSG`. Case-insensitive. Returns 200 with the id removed, 404 for an unknown id, 503 if the database is unreachable. |
| GET | `/venues/nearest?lat=&lon=` | Returns the venue closest to a coordinate and its distance in miles. Read from MongoDB; 503 if the database is unreachable. |
| GET | `/venues/by_capacity?state=&country=&limit=` | Ranks venues by capacity, largest first. All three filters are optional and combine; `state` is a state/province code, `country` a country code, `limit` a positive whole number. Read from MongoDB; 503 if the database is unreachable. |
| GET | `/teams?league=` | Lists every NBA and MLS team, keyed on `team_id`, with its `league_code` and home `venue_id`. `league` is an optional, case-insensitive league code; an unknown code returns an empty result. |
| GET | `/teams/<team_id>` | Returns one team, e.g. `/teams/NYK`. Case-insensitive; 404 for an unknown id. |
| GET | `/distance?lat1=&lon1=&lat2=&lon2=` | Returns the great-circle distance in miles between two points. |
| POST | `/road_trip` | Totals the mileage of a trip through a JSON list of venues, in order. |
| GET | `/swagger.json` | Returns the API's Swagger specification. |

Path lookups are case-insensitive and return 404 for unknown codes. Missing or invalid query parameters return 400.

**Current limitations:**
- State data currently consists of three hardcoded entries instead of records from MongoDB.
- Country, league, and team data is read from CSV files in `data/` rather than MongoDB.
- The venue endpoints read from MongoDB; the remaining collections have not been migrated yet.

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

## Seeding the Database

The venue endpoints read from MongoDB, so a fresh checkout needs its data loaded once. The CSV files in `data/` are the source of truth in version control; this step copies them into the database.

Start MongoDB first. On macOS with Homebrew:

```bash
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community
```

Then seed:

```bash
make seed
```

Expected output:

```
venues: 16 records
countries: 2 records
leagues: 2 records
teams: 16 records
```

Seeding is idempotent — each document is upserted on its natural key, so running it again refreshes the records rather than duplicating them. Re-run it after editing a CSV.

If MongoDB is not running, `make seed` exits non-zero and the venue endpoints return 503. Every other endpoint keeps working.

The test suite does not require MongoDB: it substitutes the storage layer at a seam, so `make all_tests` passes with or without a database running. To run the suite against a real seeded database instead, set `RUN_DB_INTEGRATION=1`.

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

Still to come:

- Write endpoints (POST/DELETE) for teams, and CRUD endpoints for cities and states/provinces.
- Calculating distances between two teams' home venues.
- Identifying cities with both NBA and MLS teams.
- Moving the countries, leagues, and states collections from CSV/hardcoded data into MongoDB.

## Team

- Joseph Jiminian
- Jason Legarda
- Angel Perez