"""Engine fallback must skip unreachable engines without hiding empty results."""

import time

import pytest

from app.services import job_search_service as svc


@pytest.fixture(autouse=True)
def clean_engine_state():
    svc._engine_failures.clear()
    svc._engine_blocked_until.clear()
    yield
    svc._engine_failures.clear()
    svc._engine_blocked_until.clear()


@pytest.fixture(autouse=True)
def no_google(monkeypatch):
    """These tests cover the DDGS path only.

    A real SERPER_API_KEY in .env would otherwise short-circuit _search_one
    before it ever reaches an engine, and hit the network during the suite.
    """
    monkeypatch.setattr(svc, "google_search_available", lambda: False)


class TestTransportErrorDetection:
    def test_connection_refused_is_transport_error(self):
        exc = Exception(
            "ConnectError: error sending request for url "
            "(https://www.startpage.com/) > tcp connect error > "
            "Connection refused (os error 61)"
        )
        assert svc._is_transport_error(exc)

    def test_timeout_is_transport_error(self):
        assert svc._is_transport_error(Exception("request timed out"))

    def test_empty_results_is_not_transport_error(self):
        # An empty dork result is a real answer, not a broken engine.
        assert not svc._is_transport_error(Exception("No results found."))


class TestCircuitBreaker:
    def test_engine_disabled_after_repeated_transport_failures(self):
        exc = Exception("Connection refused")
        for _ in range(svc.ENGINE_FAILURE_LIMIT):
            svc._record_engine_failure("startpage", exc)
        assert not svc._engine_available("startpage")

    def test_single_failure_keeps_engine_available(self):
        svc._record_engine_failure("brave", Exception("Connection refused"))
        assert svc._engine_available("brave")

    def test_success_clears_failures(self):
        svc._record_engine_failure("yahoo", Exception("Connection refused"))
        svc._record_engine_success("yahoo")
        assert svc._engine_failures == {}
        assert svc._engine_available("yahoo")

    def test_engine_recovers_after_cooldown(self, monkeypatch):
        exc = Exception("Connection refused")
        for _ in range(svc.ENGINE_FAILURE_LIMIT):
            svc._record_engine_failure("startpage", exc)
        assert not svc._engine_available("startpage")

        resume_at = time.monotonic() + svc.ENGINE_COOLDOWN_SECONDS + 1
        monkeypatch.setattr(svc.time, "monotonic", lambda: resume_at)
        assert svc._engine_available("startpage")


def _fake_ddgs(handler, calls: list[tuple[str, int]]):
    """Build a DDGS stub whose text() delegates to handler(backend, page)."""

    class FakeDDGS:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def text(self, query, **kwargs):
            backend = kwargs["backend"]
            page = kwargs.get("page", 1)
            calls.append((backend, page))
            return handler(backend, page)

    return FakeDDGS


class TestSearchFallback:
    def test_skips_engine_that_found_nothing_and_uses_the_next(self, monkeypatch):
        calls: list[tuple[str, int]] = []

        def handler(backend, page):
            if backend == svc.SEARCH_BACKENDS[0]:
                raise Exception("No results found.")
            if page > 1:
                raise Exception("No results found.")
            return [{"href": "https://jobs.lever.co/acme/1", "title": "Job"}]

        monkeypatch.setattr(svc, "DDGS", _fake_ddgs(handler, calls))
        results, provider = svc._search_one("site:jobs.lever.co test", 3)

        assert len(results) == 1
        # The dead engine contributes nothing to the provider label.
        assert svc.SEARCH_BACKENDS[0] not in provider
        assert svc.SEARCH_BACKENDS[1] in provider
        assert calls[0][0] == svc.SEARCH_BACKENDS[0]

    def test_merges_distinct_results_from_several_engines(self, monkeypatch):
        calls: list[tuple[str, int]] = []

        def handler(backend, page):
            if page > 1:
                raise Exception("No results found.")
            return [{"href": f"https://jobs.lever.co/acme/{backend}", "title": backend}]

        monkeypatch.setattr(svc, "DDGS", _fake_ddgs(handler, calls))
        results, provider = svc._search_one("site:jobs.lever.co test", 50)

        # Each engine indexes a different slice, so the union is what matters.
        assert len(results) == min(svc.MAX_ENGINE_ATTEMPTS, len(svc.SEARCH_BACKENDS))
        assert len({item["href"] for item in results}) == len(results)
        assert provider.startswith("ddgs:")
        assert "+" in provider

    def test_pages_an_engine_until_it_repeats_itself(self, monkeypatch):
        calls: list[tuple[str, int]] = []
        first = svc.SEARCH_BACKENDS[0]

        def handler(backend, page):
            if backend != first:
                raise Exception("No results found.")
            if page > 2:
                # Page 3 repeats page 2, which must stop the paging loop.
                return [{"href": "https://jobs.lever.co/acme/p2", "title": "p2"}]
            return [{"href": f"https://jobs.lever.co/acme/p{page}", "title": f"p{page}"}]

        monkeypatch.setattr(svc, "DDGS", _fake_ddgs(handler, calls))
        results, _ = svc._search_one("site:jobs.lever.co test", 50)

        pages = [page for backend, page in calls if backend == first]
        assert pages == [1, 2, 3]
        assert len(results) == 2

    def test_stops_paging_once_max_results_is_reached(self, monkeypatch):
        calls: list[tuple[str, int]] = []

        def handler(backend, page):
            return [
                {"href": f"https://jobs.lever.co/{backend}/{page}/{i}", "title": "j"}
                for i in range(5)
            ]

        monkeypatch.setattr(svc, "DDGS", _fake_ddgs(handler, calls))
        results, _ = svc._search_one("site:jobs.lever.co test", 5)

        assert len(results) >= 5
        assert calls == [(svc.SEARCH_BACKENDS[0], 1)]

    def test_unreachable_engine_is_skipped_on_next_query(self, monkeypatch):
        calls: list[str] = []

        class FakeDDGS:
            def __init__(self, *args, **kwargs):
                pass

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def text(self, query, **kwargs):
                calls.append(kwargs["backend"])
                raise Exception("Connection refused (os error 61)")

        monkeypatch.setattr(svc, "DDGS", FakeDDGS)

        # One blip must not disable an engine, so each needs
        # ENGINE_FAILURE_LIMIT failures before its breaker trips.
        for index in range(svc.ENGINE_FAILURE_LIMIT * len(svc.SEARCH_BACKENDS)):
            svc._search_one(f"q{index}", 3)
        calls_while_tripping = len(calls)

        svc._search_one("after-trip", 3)

        assert calls_while_tripping > 0
        # Every engine is now in cooldown, so no further requests are made.
        assert len(calls) == calls_while_tripping

    def test_returns_none_provider_when_nothing_found(self, monkeypatch):
        class FakeDDGS:
            def __init__(self, *args, **kwargs):
                pass

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def text(self, query, **kwargs):
                return []

        monkeypatch.setattr(svc, "DDGS", FakeDDGS)
        results, provider = svc._search_one("q", 3)
        assert results == []
        assert provider == "none"

    def test_attempts_are_capped(self, monkeypatch):
        calls: list[str] = []

        class FakeDDGS:
            def __init__(self, *args, **kwargs):
                pass

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def text(self, query, **kwargs):
                calls.append(kwargs["backend"])
                raise Exception("No results found.")

        monkeypatch.setattr(svc, "DDGS", FakeDDGS)
        svc._search_one("q", 3)
        assert len(calls) == svc.MAX_ENGINE_ATTEMPTS
