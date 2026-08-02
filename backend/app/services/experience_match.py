"""Strict experience-band matching for job postings.

Selected bands are inclusive year ranges. A posting is kept only when its
stated experience requirement overlaps at least one selected band. Postings
with no extractable experience requirement are dropped when the user has
picked any band — that is the "strict" behaviour.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

MATCH_EXACT = "match"
MATCH_UNKNOWN = "unknown"
MATCH_MISMATCH = "mismatch"


@dataclass(frozen=True)
class ExperienceBand:
    id: str
    label: str
    min_years: float
    max_years: float  # inclusive; use a large number for open-ended bands
    query_terms: tuple[str, ...]


EXPERIENCE_BANDS: dict[str, ExperienceBand] = {
    "0-2": ExperienceBand(
        "0-2",
        "0–2 years",
        0,
        2,
        ("0-2 years", "0-1 years", "1-2 years", "fresher", "entry level", "junior"),
    ),
    "2-5": ExperienceBand(
        "2-5",
        "2–5 years",
        2,
        5,
        ("2-5 years", "2-4 years", "3-5 years", "3+ years"),
    ),
    "5-8": ExperienceBand(
        "5-8",
        "5–8 years",
        5,
        8,
        ("5-8 years", "5-7 years", "5+ years", "6+ years"),
    ),
    "8-12": ExperienceBand(
        "8-12",
        "8–12 years",
        8,
        12,
        ("8-12 years", "8-10 years", "8+ years", "10+ years"),
    ),
    "12+": ExperienceBand(
        "12+",
        "12+ years",
        12,
        50,
        ("12+ years", "15+ years", "10-15 years", "12-15 years"),
    ),
}

BAND_ORDER = ("0-2", "2-5", "5-8", "8-12", "12+")


def resolve_bands(band_ids: list[str] | None) -> list[ExperienceBand]:
    if not band_ids:
        return []
    resolved: list[ExperienceBand] = []
    seen: set[str] = set()
    for band_id in band_ids:
        key = (band_id or "").strip()
        if key in seen or key not in EXPERIENCE_BANDS:
            continue
        seen.add(key)
        resolved.append(EXPERIENCE_BANDS[key])
    return resolved


def experience_query_clause(band_ids: list[str] | None) -> str:
    """OR of quoted experience phrases for search-engine dorks."""
    bands = resolve_bands(band_ids)
    if not bands:
        return ""
    terms: list[str] = []
    seen: set[str] = set()
    for band in bands:
        for term in band.query_terms[:3]:
            key = term.lower()
            if key in seen:
                continue
            seen.add(key)
            terms.append(f'"{term}"')
    if not terms:
        return ""
    if len(terms) == 1:
        return terms[0]
    return f"({' OR '.join(terms)})"


def _ranges_overlap(
    left_min: float, left_max: float, right_min: float, right_max: float
) -> bool:
    """True when ranges overlap by more than a shared endpoint.

    A shared endpoint alone is too weak for strict filtering — otherwise
    "Senior" (5–8) and "5+ years" would incorrectly match a 2–5 selection.
    An exact point requirement like "2 years" may still sit on a boundary.
    """
    inter_min = max(left_min, right_min)
    inter_max = min(left_max, right_max)
    if inter_min > inter_max:
        return False
    if inter_min == inter_max:
        return left_min == left_max == inter_min
    return True


def extract_experience_range(text: str) -> tuple[float, float] | None:
    """Return (min_years, max_years) required by the posting, if detectable."""
    if not text:
        return None
    lowered = text.lower()

    patterns = [
        # 2-5 years / 2 to 5 years / 2–5 yrs
        r"(\d+(?:\.\d+)?)\s*(?:-|–|—|to)\s*(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)\b",
        # 5+ years / 5 years+
        r"(\d+(?:\.\d+)?)\s*\+\s*(?:years?|yrs?)\b",
        r"(\d+(?:\.\d+)?)\s*(?:years?|yrs?)\s*\+",
        # minimum / at least / min 5 years
        r"(?:minimum|at\s+least|min(?:imum)?\.?|over|more\s+than)\s+(\d+(?:\.\d+)?)\s*(?:years?|yrs?)\b",
        # 5 years of experience / 5 yrs experience / requiring 5 years
        r"(?:require[sd]?|looking\s+for|with|having)?\s*(\d+(?:\.\d+)?)\s*(?:years?|yrs?)\s*(?:of\s+)?(?:experience|exp\.?)\b",
        # experience: 5 years
        r"(?:experience|exp\.?)\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*(?:years?|yrs?)\b",
    ]

    for pattern in patterns:
        match = re.search(pattern, lowered)
        if not match:
            continue
        groups = [float(g) for g in match.groups() if g is not None]
        if len(groups) >= 2:
            low, high = sorted(groups[:2])
            return low, high
        if len(groups) == 1:
            years = groups[0]
            # "5+ years" / "minimum 5" → open-ended upward
            if "+" in match.group(0) or re.search(
                r"minimum|at\s+least|min(?:imum)?\.?|over|more\s+than",
                match.group(0),
            ):
                return years, 50.0
            # Exact "5 years of experience" → treat as a point that can fit
            # any overlapping band.
            return years, years

    # Clear seniority signals when no numeric requirement is present.
    seniority = [
        (
            ("fresher", "entry level", "entry-level", "graduate", "intern", "junior"),
            (0.0, 2.0),
        ),
        (("mid-level", "mid level", "intermediate"), (2.0, 5.0)),
        (("senior",), (5.0, 8.0)),
        (("staff", "principal", "lead"), (8.0, 12.0)),
        (("director", "head of", "vp ", "vice president"), (12.0, 50.0)),
    ]
    for needles, band in seniority:
        if any(needle in lowered for needle in needles):
            return band

    return None


def match_experience(
    text: str,
    band_ids: list[str] | None,
) -> tuple[str, tuple[float, float] | None]:
    """Classify a posting against selected experience bands.

    Returns (verdict, extracted_range).
    """
    bands = resolve_bands(band_ids)
    extracted = extract_experience_range(text)
    if not bands:
        return MATCH_UNKNOWN, extracted

    if extracted is None:
        # Strict: if the user asked for experience bands and the posting does
        # not state one, we cannot confirm a match.
        return MATCH_UNKNOWN, None

    job_min, job_max = extracted
    for band in bands:
        if _ranges_overlap(job_min, job_max, band.min_years, band.max_years):
            return MATCH_EXACT, extracted
    return MATCH_MISMATCH, extracted
