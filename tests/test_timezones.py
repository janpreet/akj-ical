"""Timezone resolution coverage for every akj.org location."""

import zoneinfo

import pytest

import timezones

# Every entry in akj.org's location dropdown, with the timezone it must
# resolve to from the city name alone (no region given).
ALL_LOCATIONS = {
    "Adelaide": "Australia/Adelaide",
    "Agra": "Asia/Kolkata",
    "Ambala": "Asia/Kolkata",
    "Amritsar": "Asia/Kolkata",
    "AnandpurSahib": "Asia/Kolkata",
    "Atlanta": "America/New_York",
    "BabaBakala": "Asia/Kolkata",
    "Bakersfield": "America/Los_Angeles",
    "Bareilly": "Asia/Kolkata",
    "Batala": "Asia/Kolkata",
    "Bathinda": "Asia/Kolkata",
    "Bay Area": "America/Los_Angeles",
    "Bhopal": "Asia/Kolkata",
    "Birmingham": "Europe/London",
    "Boston": "America/New_York",
    "Bradford": "Europe/London",
    "Brisbane": "Australia/Brisbane",
    "Camberley": "Europe/London",
    "Canberra": "Australia/Sydney",
    "ChamkaurSahib": "Asia/Kolkata",
    "Chandigarh": "Asia/Kolkata",
    "Chchrari": "Asia/Kolkata",
    "Chicago": "America/Chicago",
    "Coventry": "Europe/London",
    "Dallas": "America/Chicago",
    "Dayalpur": "Asia/Kolkata",
    "Dayton": "America/New_York",
    "Delhi": "Asia/Kolkata",
    "Denmark": "Europe/Copenhagen",
    "Denver": "America/Denver",
    "DeraBabaNanak": "Asia/Kolkata",
    "Derby": "Europe/London",
    "Detroit": "America/Detroit",
    "Dharamkot": "Asia/Kolkata",
    "Doraha": "Asia/Kolkata",
    "Durham": "America/New_York",
    "Edmonton": "America/Edmonton",
    "FatehgarhSahib": "Asia/Kolkata",
    "France": "Europe/Paris",
    "Fresno": "America/Los_Angeles",
    "Germany": "Europe/Berlin",
    "GoindwalSahib": "Asia/Kolkata",
    "GonianaMandi": "Asia/Kolkata",
    "Gravesend": "Europe/London",
    "Gurdaspur": "Asia/Kolkata",
    "Gwalior": "Asia/Kolkata",
    "HazurSahib": "Asia/Kolkata",
    "Holland": "Europe/Amsterdam",
    "Hoshiarpur": "Asia/Kolkata",
    "Ilford": "Europe/London",
    "Indianapolis": "America/Indiana/Indianapolis",
    "Italy": "Europe/Rome",
    "Jagraon": "Asia/Kolkata",
    "Jalandhar": "Asia/Kolkata",
    "Kanpur": "Asia/Kolkata",
    "Kapurthala": "Asia/Kolkata",
    "Karnal": "Asia/Kolkata",
    "Khanna": "Asia/Kolkata",
    "Kharar": "Asia/Kolkata",
    "KumarHatti": "Asia/Kolkata",
    "Kurali": "Asia/Kolkata",
    "Las Vegas": "America/Los_Angeles",
    "Leeds": "Europe/London",
    "Leicester": "Europe/London",
    "Los Angeles": "America/Los_Angeles",
    "Lucknow": "Asia/Kolkata",
    "Ludhiana": "Asia/Kolkata",
    "MachhiwaraSahib": "Asia/Kolkata",
    "Mandi": "Asia/Kolkata",
    "Mansa": "Asia/Kolkata",
    "Melbourne": "Australia/Melbourne",
    "Moga": "Asia/Kolkata",
    "Montreal": "America/Montreal",
    "MuktsarSahib": "Asia/Kolkata",
    "Mumbai": "Asia/Kolkata",
    "NY/NJ/CT": "America/New_York",
    "NawanShahar": "Asia/Kolkata",
    "New Zealand": "Pacific/Auckland",
    "Niagara Falls": "America/Toronto",
    "Nottingham": "Europe/London",
    "Orlando": "America/New_York",
    "Ottawa": "America/Toronto",
    "Paatran": "Asia/Kolkata",
    "Panipat": "Asia/Kolkata",
    "PaontaSahib": "Asia/Kolkata",
    "Patiala": "Asia/Kolkata",
    "PatnaSahib": "Asia/Kolkata",
    "Peterborough": "Europe/London",
    "Phagwara": "Asia/Kolkata",
    "Ropar": "Asia/Kolkata",
    "Saharanpur": "Asia/Kolkata",
    "Sangrur": "Asia/Kolkata",
    "Seattle": "America/Los_Angeles",
    "Selma": "America/Los_Angeles",
    "Shepparton": "Australia/Melbourne",
    "Shimla": "Asia/Kolkata",
    "Singapore": "Asia/Singapore",
    "Sirsa": "Asia/Kolkata",
    "Slough": "Europe/London",
    "Southall": "Europe/London",
    "Spain": "Europe/Madrid",
    "Sweden": "Europe/Stockholm",
    "Sydney": "Australia/Sydney",
    "Tarantaran": "Asia/Kolkata",
    "Telford": "Europe/London",
    "Toronto": "America/Toronto",
    "UAE": "Asia/Dubai",
    "Utah": "America/Denver",
    "Vadodara": "Asia/Kolkata",
    "Vancouver": "America/Vancouver",
    "Virginia": "America/New_York",
    "Walsall": "Europe/London",
    "West Bromwich": "Europe/London",
    "Windsor": "America/Toronto",
}

# (city, region) pairs exactly as akj.org renders them, with the expected zone.
REAL_ROWS = [
    ("Ambala", "HR", "Asia/Kolkata"),
    ("Bay Area", "CA", "America/Los_Angeles"),
    ("Bradford", "North UK", "Europe/London"),
    ("Bradford", "West Yorkshire", "Europe/London"),
    ("Chandigarh", "PB", "Asia/Kolkata"),
    ("Chchrari", "PB", "Asia/Kolkata"),
    ("Coventry", "West Midlands", "Europe/London"),
    ("Delhi", "Delhi", "Asia/Kolkata"),
    ("Detroit", "MI", "America/Detroit"),
    ("Durham", "NC", "America/New_York"),
    ("Ilford", "South UK ", "Europe/London"),
    ("Indianapolis", "IN", "America/Indiana/Indianapolis"),
    ("Khanna", "PB", "Asia/Kolkata"),
    ("NY/NJ/CT", "Connecticut", "America/New_York"),
    ("NY/NJ/CT", "Delaware", "America/New_York"),
    ("NY/NJ/CT", "Massachusetts", "America/New_York"),
    ("Slough", "South UK ", "Europe/London"),
    ("Southall", "South UK ", "Europe/London"),
    ("Toronto", "ON", "America/Toronto"),
    ("Windsor", "ON", "America/Toronto"),
]


@pytest.mark.parametrize("city,expected", sorted(ALL_LOCATIONS.items()))
def test_every_location_resolves_from_city_alone(city, expected):
    assert timezones.resolve(city, "") == expected


@pytest.mark.parametrize("city,region,expected", REAL_ROWS)
def test_real_site_rows(city, region, expected):
    assert timezones.resolve(city, region) == expected


@pytest.mark.parametrize("tz", sorted(set(ALL_LOCATIONS.values())))
def test_expected_zones_exist_in_tzdata(tz):
    zoneinfo.ZoneInfo(tz)


def test_city_table_covers_the_whole_dropdown():
    missing = {c for c in ALL_LOCATIONS if c.lower() not in timezones.CITY_TZ}
    assert not missing


def test_region_beats_city_for_ambiguous_names():
    # Peterborough exists in both Ontario and the UK.
    assert timezones.resolve("Peterborough", "ON") == "America/Toronto"
    assert timezones.resolve("Peterborough", "Cambridgeshire") == "Europe/London"
    # Birmingham likewise.
    assert timezones.resolve("Birmingham", "AL") == "America/Chicago"
    assert timezones.resolve("Birmingham", "West Midlands") == "Europe/London"


def test_unknown_location_returns_none():
    assert timezones.resolve("Atlantis", "") is None
    assert timezones.resolve("", "") is None
    assert timezones.resolve(None, None) is None


def test_case_and_whitespace_insensitive():
    assert timezones.resolve("  SOUTHALL ", " south uk ") == "Europe/London"
    assert timezones.resolve("toronto", "on") == "America/Toronto"


def test_indiana_and_oregon_codes_are_us_not_india():
    assert timezones.resolve("Indianapolis", "IN") == "America/Indiana/Indianapolis"
    assert timezones.resolve("Portland", "OR") == "America/Los_Angeles"
