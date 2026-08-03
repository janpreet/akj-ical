# akj-ical

A calendar feed of the Akhand Keertan Smaagams and programs listed on
[akj.org](https://www.akj.org/programs.php), with correct timezones.

## Subscribe

```
https://raw.githubusercontent.com/janpreet/akj-ical/main/akj-programs.ics
```

Add it as a *subscribed* calendar (Apple Calendar: File → New Calendar
Subscription; Google Calendar: Other calendars → From URL) so it keeps itself
up to date. The feed rebuilds daily.

## Why this exists

akj.org already has an iCal export, but every timestamp in it is floating: it
carries a wall-clock time with no timezone. A 7:00 PM program in Ambala and a
7:00 PM program in Toronto both arrive as "7:00 PM", so a subscriber in New
York sees the Ambala smaagam at the wrong time of day.

This feed pairs each program with the venue timezone shown on the programs
listing and converts to UTC, so events land at the right instant wherever you
are. That Ambala program shows up as 9:30 AM Eastern, which is what 7:00 PM IST
actually is.

It also fixes a few things that make the upstream file unfriendly to strict
clients: a malformed `DTSTAM :2026-08-03 03:34:47` property, blank lines inside
`VEVENT` blocks, LF instead of CRLF, unescaped separators, and unfolded long
lines. Events are sorted, given globally unique UIDs, and overnight programs
listed as "8:00 PM to 2:00 AM" on a single date get an end time on the
following day rather than one seven hours before they start.

## How it works

`build_ics.py`:

1. `GET programs.php` for the listing, which renders each venue as
   "City (Region)".
2. `POST export=export` to the same URL, which returns the full upstream
   `.ics`. No login or session needed; posted bare it returns everything
   upcoming rather than the current filter.
3. Join the two on the program id, resolve a timezone via `timezones.py`,
   convert, and emit.

`timezones.py` prefers the region, because akj.org lists same-named cities in
different countries (Peterborough ON vs Peterborough UK). The city table is the
fallback and covers every entry in the site's location dropdown.

## Running it

```sh
python3 build_ics.py -o akj-programs.ics
python3 build_ics.py --strict     # exit non-zero if any venue is unmapped
```

Only the standard library is required. Tests need `pytest`.

## Tests

```sh
python3 -m pytest -q
```

Fully offline, against saved fixtures in `tests/fixtures/`. Covers every
location in akj.org's dropdown, the real "City (Region)" pairs the site
currently emits, DST boundaries in both directions, overnight rollover,
unmapped-venue fallback, and the output's iCal structure.

Enable the pre-push hook with `git config core.hooksPath .githooks`.

## When a new venue appears

akj.org adds locations over time. The daily build publishes the calendar first
and *then* fails if it met a venue it could not place, so a new city never
blocks the feed; the failing run tells you what to add to `CITY_TZ` in
`timezones.py`. Unmapped venues stay floating, which is the upstream behaviour.

## Note

Not affiliated with akj.org. The program data is theirs; this just republishes
their own export with timezones attached.
