"""Generated dorks must be shapes Google actually returns documents for."""

import pytest

from app.services import job_search_service as svc


def _perms(**overrides):
    kwargs = dict(
        site="job-boards.greenhouse.io",
        role="SDE",
        alternate_role="Software Engineer",
        location='("India")',
        skills="",
        experience='("0-2 years" OR "0-1 years" OR "1-2 years")',
        company="",
        remote_only=False,
        employment_type="",
    )
    kwargs.update(overrides)
    return svc.build_query_permutations(**kwargs)


class TestExperienceStaysOutOfQueries:
    def test_no_permutation_contains_the_experience_clause(self):
        # Requiring a literal "0-2 years" takes a query from ~10 hits to 0.
        for perm in _perms():
            assert "years" not in perm["query"].lower()

    def test_no_permutation_is_labelled_experience(self):
        labels = {perm["label"] for perm in _perms()}
        assert "experience" not in labels
        assert "exp_location" not in labels

    def test_role_and_site_survive(self):
        queries = [perm["query"] for perm in _perms()]
        assert all(q.startswith("site:job-boards.greenhouse.io") for q in queries)
        assert any('"SDE"' in q for q in queries)

    def test_internships_are_always_excluded(self):
        for perm in _perms():
            assert "-internship -intern" in perm["query"]


class TestRelaxQuery:
    def test_drops_or_groups_and_extra_quotes(self):
        query = (
            'site:job-boards.greenhouse.io "SDE" "India" '
            '("0-2 years" OR "1-2 years") -internship -intern'
        )
        assert svc.relax_query(query) == (
            'site:job-boards.greenhouse.io "SDE" India -internship -intern'
        )

    def test_keeps_the_first_phrase_quoted(self):
        relaxed = svc.relax_query('site:jobs.lever.co "Backend Engineer" "Bengaluru"')
        assert '"Backend Engineer"' in relaxed
        assert '"Bengaluru"' not in relaxed
        assert "Bengaluru" in relaxed

    def test_already_simple_query_is_unchanged(self):
        query = 'site:jobs.lever.co "Backend Engineer"'
        assert svc.relax_query(query) == query


class TestZeroResultRetry:
    @pytest.fixture(autouse=True)
    def no_google(self, monkeypatch):
        monkeypatch.setattr(svc, "google_search_available", lambda: False)
        svc._engine_failures.clear()
        svc._engine_blocked_until.clear()
        yield
        svc._engine_failures.clear()
        svc._engine_blocked_until.clear()

    def test_empty_query_is_retried_relaxed(self, monkeypatch):
        seen: list[str] = []
        strict = 'site:jobs.lever.co "SDE" "India" ("0-2 years") -internship -intern'

        def fake_run(query, max_results, date_posted):
            seen.append(query)
            if query == strict:
                return {}, []
            return (
                {"https://jobs.lever.co/acme/1": {"href": "https://jobs.lever.co/acme/1"}},
                ["ddgs:yahoo"],
            )

        monkeypatch.setattr(svc, "_run_query", fake_run)
        results, provider = svc._search_one(strict, 20)

        assert len(seen) == 2
        assert seen[1] == svc.relax_query(strict)
        assert len(results) == 1
        assert "relaxed" in provider

    def test_no_retry_when_first_attempt_finds_results(self, monkeypatch):
        seen: list[str] = []

        def fake_run(query, max_results, date_posted):
            seen.append(query)
            return (
                {"https://jobs.lever.co/acme/1": {"href": "https://jobs.lever.co/acme/1"}},
                ["ddgs:yahoo"],
            )

        monkeypatch.setattr(svc, "_run_query", fake_run)
        _, provider = svc._search_one('site:jobs.lever.co "SDE" "India"', 20)

        assert len(seen) == 1
        assert "relaxed" not in provider

    def test_returns_none_when_relaxed_also_fails(self, monkeypatch):
        monkeypatch.setattr(svc, "_run_query", lambda *a, **k: ({}, []))
        results, provider = svc._search_one('site:jobs.lever.co "SDE" "India"', 20)

        assert results == []
        assert provider == "none"
