# Data Model

The Pro Sports Venue Directory uses six collections to organize geographic information, venues, teams, and leagues.

## Countries
- `code`
- `name`

## States
- `abbrev`
- `name`
- `country_code`
- `latitude`
- `longitude`

## Cities
- `name`
- `state_abbrev`
- `latitude`
- `longitude`
- `population`

## Venues
- `venue_id`
- `name`
- `city`
- `state_code`
- `country_code`
- `capacity`
- `opened_year`
- `latitude`
- `longitude`
- `indoor`

## Teams
- `team_id`
- `name`
- `league_code`
- `venue_id`
- `founded_year`
- `conference`
- `division`

## Leagues
- `code`
- `name`
- `sport`
- `founded_year`

## Relationships

Each collection links to related records using shared codes and identifiers. States reference their country through `country_code`, cities reference their state or province through `state_abbrev`, and venues reference their location through `city`, `state_code`, and `country_code`. Teams reference their home venue using `venue_id` and their league using `league_code`.

The project focuses on NBA and MLS teams, including those based in Canada. The `countries` collection therefore includes the United States (`US`) and Canada (`CA`), while the `states` collection includes all 50 US states alongside Ontario, Quebec, and British Columbia.
