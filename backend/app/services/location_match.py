"""Match a job's real posting location against the locations the user picked.

ATS boards write locations in wildly different shapes — "India, Bangalore",
"Remote - US", "Tel Aviv", "Bengaluru, Karnataka, India". Matching is therefore
done on resolved place names rather than raw substrings, so selecting a country
still matches a posting that only names one of its cities.
"""

from __future__ import annotations

import re
import unicodedata
from functools import lru_cache

REMOTE_MARKERS = (
    "remote",
    "anywhere",
    "work from home",
    "wfh",
    "distributed",
    "virtual",
)

MATCH_EXACT = "match"
MATCH_REMOTE = "remote"
# Same country as a requested city, but a different city. Worth showing, just
# not ahead of a real match.
MATCH_COUNTRY = "country"
MATCH_UNKNOWN = "unknown"
MATCH_MISMATCH = "mismatch"

# Best to worst, for ordering results.
MATCH_ORDER = (
    MATCH_EXACT,
    MATCH_REMOTE,
    MATCH_COUNTRY,
    MATCH_UNKNOWN,
    MATCH_MISMATCH,
)


def match_rank(verdict: str) -> int:
    """Sort key: matched locations first, provable mismatches last."""
    try:
        return MATCH_ORDER.index(verdict)
    except ValueError:
        return len(MATCH_ORDER)

# Cities that ATS boards still write under an older or alternate name.
CITY_ALIASES = {
    "bengaluru": {"bangalore", "bengaluru"},
    "bangalore": {"bangalore", "bengaluru"},
    "gurugram": {"gurugram", "gurgaon"},
    "gurgaon": {"gurugram", "gurgaon"},
    "mumbai": {"mumbai", "bombay"},
    "kolkata": {"kolkata", "calcutta"},
    "chennai": {"chennai", "madras"},
    "pune": {"pune", "poona"},
    "new delhi": {"new delhi", "delhi"},
    "delhi": {"delhi", "new delhi", "ncr"},
    "noida": {"noida", "ncr"},
    "kyiv": {"kyiv", "kiev"},
    "nyc": {"nyc", "new york"},
    "new york": {"new york", "nyc", "new york city"},
    "sf": {"sf", "san francisco"},
    "san francisco": {"san francisco", "sf", "bay area"},
    "washington": {"washington", "dc", "washington dc"},
}


def _fold(text: str) -> str:
    """Lowercase and strip accents so "Malmö" and "Malmo" are one place."""
    decomposed = unicodedata.normalize("NFKD", text or "")
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch)).lower()


@lru_cache(maxsize=1)
def _geo_index() -> tuple[dict[str, str], dict[str, str]]:
    """Return (place name -> country code, country code -> country name)."""
    try:
        import geonamescache
    except Exception:
        return {}, {}

    cache = geonamescache.GeonamesCache()
    countries = cache.get_countries()
    code_to_country = {
        code: data.get("name", "") for code, data in countries.items()
    }

    place_to_code: dict[str, str] = {}

    # Larger cities win ties so "Springfield" resolves to the best-known one.
    for city in sorted(
        cache.get_cities().values(),
        key=lambda c: c.get("population", 0),
    ):
        code = city.get("countrycode", "")
        if not code:
            continue
        names = [city.get("name", "")] + list(city.get("alternatenames", []) or [])
        for raw in names:
            key = _fold(raw.strip())
            # Alternate names include stray codes and scripts; keep plain latin.
            if len(key) < 3 or not re.fullmatch(r"[a-z .'\-]+", key):
                continue
            place_to_code[key] = code

    # Countries are registered last so a country name always beats a city that
    # merely lists it as an alternate name — the Serbian city "Inđija" is
    # aliased "India", which otherwise hijacks every search for India.
    for country_code, data in countries.items():
        name = _fold(data.get("name", ""))
        if name:
            place_to_code[name] = country_code

    return place_to_code, code_to_country


def _tokens(text: str) -> list[str]:
    """Split an ATS location string into candidate place names."""
    cleaned = re.sub(r"\(.*?\)", " ", text or "")
    parts = re.split(r"[,/|;•·]+|\s+-\s+|\s{2,}", cleaned)
    return [_fold(part.strip()) for part in parts if part.strip()]


def is_remote_text(text: str) -> bool:
    lowered = (text or "").lower()
    return any(marker in lowered for marker in REMOTE_MARKERS)


def _expand(name: str) -> set[str]:
    name = _fold(name.strip())
    return CITY_ALIASES.get(name, {name})


def _country_of(name: str) -> str | None:
    place_to_code, _ = _geo_index()
    for variant in _expand(name):
        code = place_to_code.get(variant)
        if code:
            return code
    return None


def describe(text: str) -> set[str]:
    """All names and country codes a location string can be identified by."""
    identifiers: set[str] = set()
    for token in _tokens(text):
        identifiers |= _expand(token)
        code = _country_of(token)
        if code:
            identifiers.add(f"cc:{code}")
            continue

        # ATS boards glue the office onto the city — "Junglee Bangalore",
        # "Bangalore Office". Resolve the place hiding inside the token,
        # preferring the longest phrase that is a real place.
        words = token.split()
        if len(words) < 2:
            continue
        for size in (3, 2, 1):
            matched = False
            for start in range(len(words) - size + 1):
                phrase = " ".join(words[start : start + size])
                if len(phrase) < 3:
                    continue
                phrase_code = _country_of(phrase)
                if phrase_code:
                    identifiers |= _expand(phrase)
                    identifiers.add(f"cc:{phrase_code}")
                    matched = True
            if matched:
                break
    return identifiers


def _requested_names(item: dict) -> tuple[set[str], set[str]]:
    """Split one requested location into (city-level names, country names)."""
    city = (item.get("city") or "").strip()
    state = (item.get("state") or "").strip()
    country = (item.get("country") or "").strip()
    label = (item.get("label") or "").strip()

    specific: set[str] = set()
    if city:
        specific |= _expand(city)
    if state:
        specific |= _expand(state)

    countries: set[str] = set()
    if country:
        countries.add(country.lower())

    if not specific and not countries and label:
        # A bare label such as "Bengaluru" or "India": let the geo index decide
        # which of the two it is.
        for token in _tokens(label):
            if _country_of(token) and token in {
                name.lower() for name in _COUNTRY_NAMES()
            }:
                countries.add(token)
            else:
                specific |= _expand(token)

    return specific, countries


@lru_cache(maxsize=1)
def _COUNTRY_NAMES() -> frozenset[str]:
    _, code_to_country = _geo_index()
    return frozenset(name for name in code_to_country.values() if name)


def match_location(
    job_location: str | None,
    job_is_remote: bool,
    requested: list[dict],
) -> str:
    """Classify a posting against the requested locations.

    `requested` items look like {"label", "city", "country", "remote"}.
    Returns one of match / remote / unknown / mismatch.
    """
    if not requested:
        return MATCH_UNKNOWN

    wants_remote = any(
        item.get("remote")
        or is_remote_text(item.get("label", ""))
        or is_remote_text(item.get("city", ""))
        for item in requested
    )
    if wants_remote and job_is_remote:
        return MATCH_REMOTE

    if not job_location or not job_location.strip():
        return MATCH_UNKNOWN

    if is_remote_text(job_location) and wants_remote:
        return MATCH_REMOTE

    job_identifiers = describe(job_location)
    if not job_identifiers:
        return MATCH_UNKNOWN

    # Nothing in the string resolved to a real place ("Head Office"), so the
    # posting cannot be proven to be somewhere else.
    if not any(identifier.startswith("cc:") for identifier in job_identifiers):
        return MATCH_UNKNOWN

    best = MATCH_MISMATCH
    for item in requested:
        specific, countries = _requested_names(item)

        if specific & job_identifiers:
            return MATCH_EXACT

        # Country of the request, taken from the country field when given and
        # otherwise inferred from the city.
        codes = {code for code in (_country_of(name) for name in countries) if code}
        if not codes:
            codes = {
                code for code in (_country_of(name) for name in specific) if code
            }

        in_country = any(f"cc:{code}" in job_identifiers for code in codes) or bool(
            countries & job_identifiers
        )
        if in_country:
            # Asking for a whole country makes any city in it an exact match;
            # asking for a city makes its countrymen a weaker, ranked-below hit.
            if not specific:
                return MATCH_EXACT
            best = MATCH_COUNTRY

    return best
