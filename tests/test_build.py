"""Parsing, timezone conversion and iCal output, all offline against fixtures."""

import re
from datetime import datetime, timezone
from pathlib import Path

import pytest

import build_ics
import timezones

FIXTURES = Path(__file__).parent / "fixtures"
HTML = (FIXTURES / "programs.html").read_text(encoding="utf-8", errors="replace")
EXPORT = (FIXTURES / "export.ics").read_text(encoding="utf-8", errors="replace")
NOW = datetime(2026, 8, 3, 10, 34, 47, tzinfo=timezone.utc)


@pytest.fixture(scope="module")
def built():
    return build_ics.build(HTML, EXPORT, now=NOW)


# --- parsing ---------------------------------------------------------------

def test_parses_every_event_in_the_export():
    events = build_ics.parse_events(EXPORT)
    assert len(events) == EXPORT.count("BEGIN:VEVENT") == 61
    assert all(e["UID"] and e["DTSTART"] for e in events)


def test_parses_a_location_for_every_event():
    locations = build_ics.parse_locations(HTML)
    uids = {e["UID"] for e in build_ics.parse_events(EXPORT)}
    assert uids <= set(locations)


def test_known_event_fields():
    events = {e["UID"]: e for e in build_ics.parse_events(EXPORT)}
    southall = events["4496"]
    assert southall["SUMMARY"] == "Akhand Keertan Smaagam at Southall"
    assert southall["DTSTART"] == "20260804T180000"
    assert southall["DTEND"] == "20260809T043000"
    assert build_ics.parse_locations(HTML)["4496"] == ("Southall", "South UK ")


def test_url_property_with_parameters_is_parsed():
    events = {e["UID"]: e for e in build_ics.parse_events(EXPORT)}
    assert events["4496"]["URL"].endswith("programdetail.php?q=NDQ5Ng==")


# --- timezone conversion ---------------------------------------------------

def test_every_event_resolves_a_timezone(built):
    _, warnings = built
    assert warnings == []


def test_ambala_and_toronto_diverge_in_utc(built):
    """The whole point: identical wall-clock times must not collapse."""
    ist = build_ics.to_utc(datetime(2026, 8, 13, 19, 0), "Asia/Kolkata")
    est = build_ics.to_utc(datetime(2026, 8, 13, 19, 0), "America/Toronto")
    assert ist == "20260813T133000Z"  # IST is UTC+5:30
    assert est == "20260813T230000Z"  # EDT is UTC-4 in August
    assert ist != est


def test_conversion_honours_dst_transitions():
    # New York is UTC-4 in summer, UTC-5 in winter.
    assert build_ics.to_utc(datetime(2026, 7, 1, 12, 0), "America/New_York") == (
        "20260701T160000Z"
    )
    assert build_ics.to_utc(datetime(2026, 12, 1, 12, 0), "America/New_York") == (
        "20261201T170000Z"
    )
    # India has no DST, so both are +5:30.
    assert build_ics.to_utc(datetime(2026, 7, 1, 12, 0), "Asia/Kolkata") == (
        "20260701T063000Z"
    )
    assert build_ics.to_utc(datetime(2026, 12, 1, 12, 0), "Asia/Kolkata") == (
        "20261201T063000Z"
    )


def test_ambala_event_lands_at_the_right_utc_instant(built):
    ics, _ = built
    block = _event_block(ics, "4637")  # Ambala, 2026-08-13 19:00 IST
    assert "DTSTART:20260813T133000Z" in block


def test_overnight_event_end_rolls_to_next_day():
    export = _single_event(dtstart="20260808T200000", dtend="20260808T020000")
    ics, _ = build_ics.build(HTML, export, now=NOW)
    block = _event_block(ics, "4586")
    start = re.search(r"DTSTART:(\S+)", block).group(1)
    end = re.search(r"DTEND:(\S+)", block).group(1)
    assert end > start
    assert end.startswith("20260809")


def test_same_day_event_is_left_alone():
    export = _single_event(dtstart="20260808T050000", dtend="20260808T120000")
    ics, _ = build_ics.build(HTML, export, now=NOW)
    block = _event_block(ics, "4586")
    assert re.search(r"DTEND:(\S+)", block).group(1).startswith("20260808")


def test_unresolved_location_stays_floating_and_warns():
    export = _single_event(uid="999999")
    ics, warnings = build_ics.build(HTML, export, now=NOW)
    assert any("999999" in w for w in warnings)
    block = _event_block(ics, "999999")
    assert "DTSTART:20260808T200000" in block  # no trailing Z


# --- output shape ----------------------------------------------------------

def test_calendar_envelope(built):
    ics, _ = built
    assert ics.startswith("BEGIN:VCALENDAR\r\n")
    assert ics.endswith("END:VCALENDAR\r\n")
    assert "VERSION:2.0" in ics
    assert ics.count("BEGIN:VEVENT") == ics.count("END:VEVENT") == 61


def test_crlf_line_endings_and_no_blank_lines(built):
    ics, _ = built
    assert "\n" not in ics.replace("\r\n", "")
    assert all(line for line in ics.split("\r\n")[:-1])


def test_no_malformed_dtstamp(built):
    """akj.org emits 'DTSTAM :2026-08-03 03:34:47', which breaks strict clients."""
    ics, _ = built
    assert "DTSTAM " not in ics
    assert ics.count("DTSTAMP:20260803T103447Z") == 61


def test_uids_are_globally_qualified_and_unique(built):
    ics, _ = built
    uids = [u.strip() for u in re.findall(r"^UID:(.+)$", ics, re.M)]
    assert len(uids) == len(set(uids)) == 61
    assert all(u.endswith("@akj.org") for u in uids)


def test_events_are_sorted_by_start(built):
    ics, _ = built
    starts = re.findall(r"^DTSTART:(\S+)$", ics, re.M)
    assert starts == sorted(starts)


def test_lines_are_folded_to_75_octets(built):
    ics, _ = built
    assert all(len(line.encode()) <= 75 for line in ics.split("\r\n"))


def test_folded_lines_unfold_back_to_the_original(built):
    ics, _ = built
    unfolded = ics.replace("\r\n ", "")
    assert "SUMMARY:Akhand Keertan Smaagam at Southall" in unfolded


def test_special_characters_are_escaped():
    assert build_ics._escape("a,b;c\\d") == "a\\,b\\;c\\\\d"
    assert build_ics._escape("line1\nline2") == "line1\\nline2"


def test_location_includes_city_and_region(built):
    ics, _ = built
    block = _event_block(ics, "4496").replace("\r\n ", "")
    assert "Southall (South UK )" in block


def test_description_states_the_local_time(built):
    ics, _ = built
    block = _event_block(ics, "4637").replace("\r\n ", "")
    assert "Local start: 2026-08-13 07:00 PM Asia/Kolkata" in block


def test_url_is_preserved(built):
    ics, _ = built
    block = _event_block(ics, "4496").replace("\r\n ", "")
    assert "URL;VALUE=URI:https://www.akj.org/programdetail.php?q=NDQ5Ng==" in block


def test_build_is_deterministic():
    first, _ = build_ics.build(HTML, EXPORT, now=NOW)
    second, _ = build_ics.build(HTML, EXPORT, now=NOW)
    assert first == second


def test_every_event_in_output_has_required_properties(built):
    ics, _ = built
    for block in ics.split("BEGIN:VEVENT")[1:]:
        for prop in ("UID:", "DTSTAMP:", "DTSTART:", "DTEND:", "SUMMARY:"):
            assert prop in block


def test_fixture_locations_all_resolve():
    """Guards the timezone table against the real listing, not just unit cases."""
    for uid, (city, region) in build_ics.parse_locations(HTML).items():
        assert timezones.resolve(city, region) is not None, f"{uid}: {city} ({region})"


# --- helpers ---------------------------------------------------------------

def _event_block(ics, uid):
    for block in ics.split("BEGIN:VEVENT")[1:]:
        if f"UID:{uid}@akj.org" in block:
            return block
    raise AssertionError(f"event {uid} not in output")


def _single_event(uid="4586", dtstart="20260808T200000", dtend="20260808T020000"):
    return (
        "BEGIN:VCALENDAR\n"
        "BEGIN:VEVENT\n"
        f"UID:{uid}\n"
        f"DTSTART:{dtstart}\n"
        f"DTEND:{dtend}\n"
        "SUMMARY:Test Program\n"
        "END:VEVENT\n"
        "END:VCALENDAR\n"
    )
