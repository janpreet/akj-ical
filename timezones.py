"""Resolve an akj.org program location to an IANA timezone.

akj.org renders each program's place as "City (Region)", e.g. "Ambala (HR)",
"NY/NJ/CT (Connecticut)", "Southall (South UK )".

The region is checked first because it disambiguates cities that exist in more
than one country: akj.org lists both "Peterborough (ON)" and Peterborough in
the UK. The city table is the fallback for rows whose region is missing or
unrecognised, and covers every location in akj.org's location dropdown.
"""

# Every entry in akj.org's location dropdown (114 as of 2026-08).
CITY_TZ = {
    # India
    "agra": "Asia/Kolkata",
    "ambala": "Asia/Kolkata",
    "amritsar": "Asia/Kolkata",
    "anandpursahib": "Asia/Kolkata",
    "bababakala": "Asia/Kolkata",
    "bareilly": "Asia/Kolkata",
    "batala": "Asia/Kolkata",
    "bathinda": "Asia/Kolkata",
    "bhopal": "Asia/Kolkata",
    "chamkaursahib": "Asia/Kolkata",
    "chandigarh": "Asia/Kolkata",
    "chchrari": "Asia/Kolkata",
    "dayalpur": "Asia/Kolkata",
    "delhi": "Asia/Kolkata",
    "derababananak": "Asia/Kolkata",
    "dharamkot": "Asia/Kolkata",
    "doraha": "Asia/Kolkata",
    "fatehgarhsahib": "Asia/Kolkata",
    "goindwalsahib": "Asia/Kolkata",
    "gonianamandi": "Asia/Kolkata",
    "gurdaspur": "Asia/Kolkata",
    "gwalior": "Asia/Kolkata",
    "hazursahib": "Asia/Kolkata",
    "hoshiarpur": "Asia/Kolkata",
    "jagraon": "Asia/Kolkata",
    "jalandhar": "Asia/Kolkata",
    "kanpur": "Asia/Kolkata",
    "kapurthala": "Asia/Kolkata",
    "karnal": "Asia/Kolkata",
    "khanna": "Asia/Kolkata",
    "kharar": "Asia/Kolkata",
    "kumarhatti": "Asia/Kolkata",
    "kurali": "Asia/Kolkata",
    "lucknow": "Asia/Kolkata",
    "ludhiana": "Asia/Kolkata",
    "machhiwarasahib": "Asia/Kolkata",
    "mandi": "Asia/Kolkata",
    "mansa": "Asia/Kolkata",
    "moga": "Asia/Kolkata",
    "muktsarsahib": "Asia/Kolkata",
    "mumbai": "Asia/Kolkata",
    "nawanshahar": "Asia/Kolkata",
    "paatran": "Asia/Kolkata",
    "panipat": "Asia/Kolkata",
    "paontasahib": "Asia/Kolkata",
    "patiala": "Asia/Kolkata",
    "patnasahib": "Asia/Kolkata",
    "phagwara": "Asia/Kolkata",
    "ropar": "Asia/Kolkata",
    "saharanpur": "Asia/Kolkata",
    "sangrur": "Asia/Kolkata",
    "shimla": "Asia/Kolkata",
    "sirsa": "Asia/Kolkata",
    "tarantaran": "Asia/Kolkata",
    "vadodara": "Asia/Kolkata",
    # UK
    "birmingham": "Europe/London",
    "bradford": "Europe/London",
    "camberley": "Europe/London",
    "coventry": "Europe/London",
    "derby": "Europe/London",
    "gravesend": "Europe/London",
    "ilford": "Europe/London",
    "leeds": "Europe/London",
    "leicester": "Europe/London",
    "nottingham": "Europe/London",
    "peterborough": "Europe/London",
    "slough": "Europe/London",
    "southall": "Europe/London",
    "telford": "Europe/London",
    "walsall": "Europe/London",
    "west bromwich": "Europe/London",
    # Europe (listed by country, not city)
    "denmark": "Europe/Copenhagen",
    "france": "Europe/Paris",
    "germany": "Europe/Berlin",
    "holland": "Europe/Amsterdam",
    "italy": "Europe/Rome",
    "spain": "Europe/Madrid",
    "sweden": "Europe/Stockholm",
    # USA
    "atlanta": "America/New_York",
    "bakersfield": "America/Los_Angeles",
    "bay area": "America/Los_Angeles",
    "boston": "America/New_York",
    "chicago": "America/Chicago",
    "dallas": "America/Chicago",
    "dayton": "America/New_York",
    "denver": "America/Denver",
    "detroit": "America/Detroit",
    "durham": "America/New_York",
    "fresno": "America/Los_Angeles",
    "indianapolis": "America/Indiana/Indianapolis",
    "las vegas": "America/Los_Angeles",
    "los angeles": "America/Los_Angeles",
    "ny/nj/ct": "America/New_York",
    "orlando": "America/New_York",
    "seattle": "America/Los_Angeles",
    "selma": "America/Los_Angeles",
    "utah": "America/Denver",
    "virginia": "America/New_York",
    # Canada
    "edmonton": "America/Edmonton",
    "montreal": "America/Montreal",
    "niagara falls": "America/Toronto",
    "ottawa": "America/Toronto",
    "toronto": "America/Toronto",
    "vancouver": "America/Vancouver",
    "windsor": "America/Toronto",
    # Australia / NZ / Asia
    "adelaide": "Australia/Adelaide",
    "brisbane": "Australia/Brisbane",
    "canberra": "Australia/Sydney",
    "melbourne": "Australia/Melbourne",
    "new zealand": "Pacific/Auckland",
    "shepparton": "Australia/Melbourne",
    "singapore": "Asia/Singapore",
    "sydney": "Australia/Sydney",
    "uae": "Asia/Dubai",
}

# Indian state codes and names seen in the region field.
INDIA = {
    "pb", "hr", "hp", "up", "mh", "mp", "rj", "gj", "dl", "delhi", "punjab",
    "haryana", "himachalpradesh", "uttarpradesh", "madhyapradesh", "gujarat",
    "maharashtra", "rajasthan", "bihar", "br", "uttarakhand", "jk", "ch",
    "chandigarh", "wb", "ka", "tn", "ap", "ts", "or", "od", "jh", "cg", "as",
}

# UK regions, matched as substrings so "South UK" and "West Yorkshire" both hit.
UK_TOKENS = (
    "uk", "yorkshire", "midlands", "london", "england", "scotland", "wales",
    "surrey", "kent", "essex", "berkshire", "shropshire", "staffordshire",
    "lancashire", "leicestershire", "nottinghamshire", "derbyshire",
    "cambridgeshire", "buckinghamshire",
)

CANADA = {
    "on": "America/Toronto",
    "ontario": "America/Toronto",
    "qc": "America/Montreal",
    "quebec": "America/Montreal",
    "ab": "America/Edmonton",
    "alberta": "America/Edmonton",
    "bc": "America/Vancouver",
    "britishcolumbia": "America/Vancouver",
    "mb": "America/Winnipeg",
    "manitoba": "America/Winnipeg",
    "sk": "America/Regina",
}

_US_EASTERN = (
    "ct connecticut ny newyork nj newjersey pa pennsylvania ma massachusetts "
    "de delaware md maryland va virginia wv westvirginia nc northcarolina "
    "sc southcarolina ga georgia fl florida oh ohio ri rhodeisland vt vermont "
    "nh newhampshire me maine dc"
)
_US_CENTRAL = (
    "il illinois tx texas wi wisconsin mn minnesota ia iowa mo missouri "
    "ar arkansas la louisiana ok oklahoma ks kansas ne nebraska sd northdakota "
    "nd southdakota al alabama ms mississippi tn tennessee ky kentucky"
)
_US_MOUNTAIN = "co colorado ut utah nm newmexico wy wyoming mt montana id idaho"
_US_PACIFIC = "ca california wa washington or oregon nv nevada"

US = {}
for _codes, _tz in (
    (_US_EASTERN, "America/New_York"),
    (_US_CENTRAL, "America/Chicago"),
    (_US_MOUNTAIN, "America/Denver"),
    (_US_PACIFIC, "America/Los_Angeles"),
):
    for _code in _codes.split():
        US[_code] = _tz
US["mi"] = "America/Detroit"
US["michigan"] = "America/Detroit"
US["in"] = "America/Indiana/Indianapolis"
US["indiana"] = "America/Indiana/Indianapolis"
US["az"] = "America/Phoenix"
US["arizona"] = "America/Phoenix"
US["ak"] = "America/Anchorage"
US["alaska"] = "America/Anchorage"
US["hi"] = "Pacific/Honolulu"
US["hawaii"] = "Pacific/Honolulu"

# "or" (Oregon) and "in" (Indiana) also read as Indian state codes and English
# words. akj.org has no Oregon or generic-"in" rows, and the region field is
# always a place, so US wins for these two; India keeps the rest.
INDIA -= {"or", "in"}


def resolve(city, region):
    """Return an IANA timezone name, or None if the location is unrecognised.

    Region is authoritative when recognised, since akj.org lists same-named
    cities in different countries (Peterborough ON vs Peterborough UK).
    """
    city = (city or "").strip().lower()
    region = (region or "").strip().lower()
    key = region.replace(" ", "").replace(".", "")

    if key in CANADA:
        return CANADA[key]
    if key in US:
        return US[key]
    if key in INDIA:
        return "Asia/Kolkata"
    if region and any(token in region for token in UK_TOKENS):
        return "Europe/London"
    if city in CITY_TZ:
        return CITY_TZ[city]
    return None
