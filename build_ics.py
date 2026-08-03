#!/usr/bin/env python3
"""Rebuild an akj.org program calendar with real timezones.

akj.org already exposes an iCal export (POST export=export to programs.php),
but every time in it is floating: a 6:00 PM program in Ambala and one in
Toronto both render as 6:00 PM on the subscriber's device. This script pairs
each event with the venue timezone shown on programs.php, converts to UTC, and
emits a spec-clean .ics so subscribers see correct local times.
"""

import argparse
import base64
import re
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import timezones

PROGRAMS_URL = "https://www.akj.org/programs.php"
USER_AGENT = "akj-ical/1.0 (+https://github.com/janpreet/akj-ical)"


def _get(data=None):
    req = urllib.request.Request(
        PROGRAMS_URL, data=data, headers={"User-Agent": USER_AGENT}
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8", errors="replace")


def fetch_html():
    return _get()


def fetch_export():
    return _get(data=b"export=export")


def parse_locations(html):
    """Map program UID -> (city, region) from the programs.php listing."""
    out = {}
    # The listing is emitted as one long line, so anchor on each program block
    # rather than letting a regex run across neighbouring events.
    for block in html.split('<div class="prog-div-rep">')[1:]:
        match = re.search(
            r'<h4 class="prog-name"><a href="programdetail\.php\?q=([A-Za-z0-9=]+)"',
            block,
        )
        if not match:
            continue
        try:
            uid = base64.b64decode(match.group(1)).decode()
        except Exception:
            continue
        places = re.findall(r'<h4 class="prog-st">([^<]*)</h4>', block)
        if not places:
            continue
        # The last prog-st row is "City (Region)"; earlier ones are the street.
        match = re.match(r"\s*(.*?)\s*\(([^)]*)\)\s*$", places[-1])
        if match:
            out[uid] = (match.group(1), match.group(2))
        else:
            out[uid] = (places[-1].strip(), "")
    return out


def parse_events(ics_text):
    """Parse akj.org's export into dicts. Tolerates its DTSTAM typo."""
    events = []
    current = None
    for line in ics_text.splitlines():
        line = line.strip()
        if line == "BEGIN:VEVENT":
            current = {}
        elif line == "END:VEVENT":
            if current and current.get("UID"):
                events.append(current)
            current = None
        elif current is not None and ":" in line:
            name, value = line.split(":", 1)
            current[name.split(";")[0].strip()] = value
    return events


def _parse_floating(value):
    return datetime.strptime(value.strip(), "%Y%m%dT%H%M%S")


def to_utc(naive, tz_name):
    return (
        naive.replace(tzinfo=ZoneInfo(tz_name))
        .astimezone(timezone.utc)
        .strftime("%Y%m%dT%H%M%SZ")
    )


def _escape(text):
    return (
        text.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\r\n", "\\n")
        .replace("\n", "\\n")
    )


def _fold(line):
    """RFC 5545 content lines are limited to 75 octets."""
    encoded = line.encode("utf-8")
    if len(encoded) <= 75:
        return [line]
    parts, chunk = [], b""
    limit = 75
    for char in line:
        char_bytes = char.encode("utf-8")
        if len(chunk) + len(char_bytes) > limit:
            parts.append(chunk.decode("utf-8"))
            chunk = b" " + char_bytes
            limit = 74
        else:
            chunk += char_bytes
    if chunk:
        parts.append(chunk.decode("utf-8"))
    return parts


def build(html, ics_text, now=None):
    """Return (ics_string, warnings)."""
    locations = parse_locations(html)
    stamp = (now or datetime.now(timezone.utc)).strftime("%Y%m%dT%H%M%SZ")
    warnings = []

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//janpreet//akj-ical//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:AKJ.org Programs",
        "X-WR-CALDESC:Akhand Keertan Smaagams and programs listed on akj.org",
        "REFRESH-INTERVAL;VALUE=DURATION:PT12H",
        "X-PUBLISHED-TTL:PT12H",
    ]

    for event in sorted(parse_events(ics_text), key=lambda e: e.get("DTSTART", "")):
        uid = event["UID"]
        if not event.get("DTSTART"):
            warnings.append(f"{uid}: no DTSTART, skipped")
            continue

        city, region = locations.get(uid, ("", ""))
        tz_name = timezones.resolve(city, region)
        if tz_name is None:
            warnings.append(
                f"{uid}: unresolved timezone for {city!r} ({region!r}), left floating"
            )

        start = _parse_floating(event["DTSTART"])
        end = _parse_floating(event["DTEND"]) if event.get("DTEND") else start
        # Overnight keertan is listed as e.g. 8:00 PM to 2:00 AM on one date.
        if end <= start:
            end += timedelta(days=1)

        lines.append("BEGIN:VEVENT")
        lines.append(f"UID:{uid}@akj.org")
        lines.append(f"DTSTAMP:{stamp}")
        if tz_name:
            lines.append(f"DTSTART:{to_utc(start, tz_name)}")
            lines.append(f"DTEND:{to_utc(end, tz_name)}")
        else:
            lines.append(f"DTSTART:{start:%Y%m%dT%H%M%S}")
            lines.append(f"DTEND:{end:%Y%m%dT%H%M%S}")
        lines.append(f"SUMMARY:{_escape(event.get('SUMMARY', 'AKJ Program'))}")

        place = event.get("LOCATION", "").strip()
        if city:
            place = f"{place}, {city} ({region})" if place else f"{city} ({region})"
        if place:
            lines.append(f"LOCATION:{_escape(place)}")

        description = event.get("DESCRIPTION", "").strip()
        if tz_name:
            local = f"Local start: {start:%Y-%m-%d %I:%M %p} {tz_name}"
            description = f"{description}\\n\\n{local}" if description else local
        if description:
            lines.append(f"DESCRIPTION:{description}")

        url = event.get("URL", "").strip()
        if url:
            lines.append(f"URL;VALUE=URI:{url}")
        lines.append("END:VEVENT")

    lines.append("END:VCALENDAR")

    folded = []
    for line in lines:
        folded.extend(_fold(line))
    return "\r\n".join(folded) + "\r\n", warnings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-o", "--output", default="akj-programs.ics")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit non-zero if any event's timezone could not be resolved",
    )
    parser.add_argument(
        "--min-events",
        type=int,
        default=1,
        help="refuse to write the calendar if fewer events than this were found",
    )
    args = parser.parse_args()

    html = fetch_html()
    export = fetch_export()
    print(f"fetched listing: {len(html)} bytes, export: {len(export)} bytes")
    print(f"listing blocks: {html.count('prog-div-rep')}, "
          f"export events: {export.count('BEGIN:VEVENT')}")

    ics, warnings = build(html, export)
    count = ics.count("BEGIN:VEVENT")

    # An empty or suspiciously small result means akj.org served us something
    # other than the listing. Never overwrite a good calendar with that.
    if count < args.min_events:
        print(
            f"ERROR: only {count} events (need {args.min_events}); "
            "refusing to write. akj.org may have blocked or changed the page.",
            file=sys.stderr,
        )
        return 2

    with open(args.output, "w", encoding="utf-8", newline="") as handle:
        handle.write(ics)

    print(f"wrote {args.output}: {count} events")
    for warning in warnings:
        print(f"WARNING: {warning}", file=sys.stderr)
    if warnings and args.strict:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
