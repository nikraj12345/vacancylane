"""Fetch Google organic results into the app.

google.com itself cannot be scraped from a server — every no-JS fetch returns a
JavaScript gate. The only reliable way to put Google's index into this project
is a SERP API that already queries Google for us:

1. Serper (https://serper.dev) — preferred. 2,500 free queries on signup, no
   credit card. Returns real Google organic results as JSON.
2. Google Programmable Search (Custom Search JSON API) — official Google API,
   100 free queries/day, then paid.

When neither key is configured, callers fall back to DDGS.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger("uvicorn.error")

SERPER_URL = "https://google.serper.dev/search"
GOOGLE_CSE_URL = "https://www.googleapis.com/customsearch/v1"

# Free Serper accounts reject any request carrying "num" with
# "Query pattern not allowed for free accounts", so volume has to come from
# paging: one page is a fixed 10 organic results.
SERPER_PAGE_SIZE = 10
CSE_PAGE_SIZE = 10
MAX_GOOGLE_PAGES = 4

_DATE_TBS = {
    "day": "qdr:d",
    "week": "qdr:w",
    "month": "qdr:m",
    "year": "qdr:y",
}


def google_providers_configured() -> list[str]:
    """Names of Google providers that have credentials in settings."""
    providers: list[str] = []
    if settings.serper_api_key.strip():
        providers.append("serper")
    if settings.google_api_key.strip() and settings.google_search_engine_id.strip():
        providers.append("google_cse")
    return providers


def google_search_available() -> bool:
    return bool(google_providers_configured())


def search_google(
    query: str,
    max_results: int = 20,
    date_posted: str = "month",
) -> tuple[list[dict[str, Any]], str]:
    """Return (results, provider_label). Empty list when nothing is configured."""
    if settings.serper_api_key.strip():
        results = _search_serper(query, max_results, date_posted)
        if results:
            return results, "google:serper"
        # Fall through to CSE if Serper returned nothing but CSE is configured.

    if settings.google_api_key.strip() and settings.google_search_engine_id.strip():
        results = _search_cse(query, max_results, date_posted)
        if results:
            return results, "google:cse"

    return [], "none"


def _normalize_item(title: str, link: str, snippet: str) -> dict[str, Any] | None:
    href = (link or "").strip()
    if not href.startswith("http"):
        return None
    return {
        "title": (title or "").strip() or href,
        "href": href,
        "body": (snippet or "").strip(),
    }


import time
from threading import Lock

_serper_lock = Lock()
_serper_blocked_until = 0.0
SERPER_COOLDOWN_SECONDS = 300.0

def _search_serper(
    query: str, max_results: int, date_posted: str
) -> list[dict[str, Any]]:
    global _serper_blocked_until
    with _serper_lock:
        if time.monotonic() < _serper_blocked_until:
            return []

    collected: dict[str, dict[str, Any]] = {}
    tbs = _DATE_TBS.get(date_posted)
    headers = {
        "X-API-KEY": settings.serper_api_key.strip(),
        "Content-Type": "application/json",
    }

    for page in range(1, MAX_GOOGLE_PAGES + 1):
        if len(collected) >= max_results:
            break
        # Deliberately no "num": free accounts 400 on it. Paging is the only
        # way to go past the fixed 10 results per response.
        payload: dict[str, Any] = {"q": query, "page": page, "hl": "en"}
        if tbs:
            payload["tbs"] = tbs

        try:
            with httpx.Client(timeout=12.0) as client:
                response = client.post(SERPER_URL, headers=headers, json=payload)
            if response.status_code == 401:
                logger.warning("Serper rejected the API key (401)")
                with _serper_lock:
                    _serper_blocked_until = time.monotonic() + SERPER_COOLDOWN_SECONDS
                break
            if response.status_code == 429:
                logger.warning("Serper rate/quota limit hit (429) - cooling down for 5 mins")
                with _serper_lock:
                    _serper_blocked_until = time.monotonic() + SERPER_COOLDOWN_SECONDS
                break
            if response.status_code == 400:
                logger.warning("Serper rejected the query | %s", response.text[:200])
                break
            response.raise_for_status()
            data = response.json()
        except Exception as exc:
            logger.warning("Serper request failed | page=%d | %s", page, exc)
            break

        organic = data.get("organic") or []
        if not organic:
            break

        fresh = 0
        for item in organic:
            normalized = _normalize_item(
                item.get("title", ""),
                item.get("link", ""),
                item.get("snippet", ""),
            )
            if normalized and normalized["href"] not in collected:
                collected[normalized["href"]] = normalized
                fresh += 1

        if fresh == 0:
            break

    if collected:
        logger.info(
            "GOOGLE serper | query=%r | hits=%d", query, len(collected)
        )
    return list(collected.values())[:max_results]


def _search_cse(
    query: str, max_results: int, date_posted: str
) -> list[dict[str, Any]]:
    collected: dict[str, dict[str, Any]] = {}
    date_restrict = {
        "day": "d1",
        "week": "w1",
        "month": "m1",
        "year": "y1",
    }.get(date_posted)

    # CSE allows start=1,11,21,... and num<=10.
    for page in range(MAX_GOOGLE_PAGES):
        if len(collected) >= max_results:
            break
        start = page * CSE_PAGE_SIZE + 1
        params: dict[str, Any] = {
            "key": settings.google_api_key.strip(),
            "cx": settings.google_search_engine_id.strip(),
            "q": query,
            "num": CSE_PAGE_SIZE,
            "start": start,
            "hl": "en",
        }
        if date_restrict:
            params["dateRestrict"] = date_restrict

        try:
            with httpx.Client(timeout=12.0) as client:
                response = client.get(GOOGLE_CSE_URL, params=params)
            if response.status_code in {401, 403}:
                logger.warning(
                    "Google CSE auth/quota error (%s)", response.status_code
                )
                break
            response.raise_for_status()
            data = response.json()
        except Exception as exc:
            logger.warning("Google CSE request failed | start=%d | %s", start, exc)
            break

        items = data.get("items") or []
        if not items:
            break

        fresh = 0
        for item in items:
            normalized = _normalize_item(
                item.get("title", ""),
                item.get("link", ""),
                item.get("snippet", ""),
            )
            if normalized and normalized["href"] not in collected:
                collected[normalized["href"]] = normalized
                fresh += 1

        if fresh == 0:
            break

    if collected:
        logger.info("GOOGLE cse | query=%r | hits=%d", query, len(collected))
    return list(collected.values())[:max_results]
