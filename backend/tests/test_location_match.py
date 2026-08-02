"""Location is reported on every job and never used to drop one."""

import pytest

from app.services.job_search_service import annotate_locations, _is_junk_title
from app.services.location_match import (
    MATCH_EXACT,
    MATCH_MISMATCH,
    MATCH_REMOTE,
    MATCH_UNKNOWN,
    match_location,
)

BENGALURU = [
    {"label": "Bengaluru", "city": "Bengaluru", "state": "Karnataka", "country": "India"}
]
INDIA = [{"label": "India", "city": "", "state": "", "country": "India"}]
REMOTE = [{"label": "Remote", "city": "", "country": "", "remote": True}]


class TestMatchLocation:
    @pytest.mark.parametrize(
        "job_location",
        [
            "India, Bangalore",
            "Bengaluru, Karnataka, India",
            "Bangalore",
            "BENGALURU, IN",
        ],
    )
    def test_city_variants_match(self, job_location):
        assert match_location(job_location, False, BENGALURU) == MATCH_EXACT

    def test_country_selection_matches_a_city_in_that_country(self):
        # Selecting "India" must still match a posting that only names a city.
        assert match_location("Mumbai", False, INDIA) == MATCH_EXACT

    def test_other_country_is_a_mismatch(self):
        assert match_location("Tel Aviv", False, BENGALURU) == MATCH_MISMATCH
        assert match_location("Barcelona, Spain", False, INDIA) == MATCH_MISMATCH

    def test_remote_request_matches_remote_posting(self):
        assert match_location("Remote - US", True, REMOTE) == MATCH_REMOTE

    def test_missing_location_is_unknown_not_mismatch(self):
        assert match_location(None, False, BENGALURU) == MATCH_UNKNOWN
        assert match_location("", False, BENGALURU) == MATCH_UNKNOWN

    def test_no_requested_locations_is_unknown(self):
        assert match_location("Anywhere", False, []) == MATCH_UNKNOWN


class TestJunkTitles:
    @pytest.mark.parametrize(
        "title",
        [
            "nvidia.wd5.myworkdayjobs.com/en-US/NVIDIAExternalCareerSite/job/x",
            "https://jobs.lever.co/acme",
            "Careers",
            "jobs",
            "",
        ],
    )
    def test_rejects_junk(self, title):
        assert _is_junk_title(title)

    @pytest.mark.parametrize(
        "title",
        [
            "Senior AI Engineer",
            "AI Engineer - Agentic AI & Automation",
            "Backend Engineer (Python/FastAPI)",
        ],
    )
    def test_keeps_real_titles(self, title):
        assert not _is_junk_title(title)


class TestApplyLocationFilter:
    def _job(self, **kwargs):
        base = {"title": "AI Engineer", "snippet": "", "is_remote": False}
        base.update(kwargs)
        return base

    def test_labels_every_job_without_dropping_mismatches(self):
        jobs = [
            self._job(location="Bengaluru, India"),
            self._job(location="Tel Aviv, Israel"),
            self._job(location=None),
        ]
        kept = annotate_locations(jobs, BENGALURU)

        # Nothing is filtered out; the verdict is reported instead.
        assert len(kept) == 3
        assert [job["location_match"] for job in kept] == [
            MATCH_EXACT,
            MATCH_MISMATCH,
            MATCH_UNKNOWN,
        ]

    def test_without_requested_locations_everything_is_unknown(self):
        jobs = [self._job(location="Tel Aviv"), self._job(location="Berlin")]
        kept = annotate_locations(jobs, [])
        assert len(kept) == 2
        assert all(job["location_match"] == MATCH_UNKNOWN for job in kept)

    def test_junk_titles_are_always_dropped(self):
        jobs = [self._job(title="Careers", location="Bengaluru, India")]
        assert annotate_locations(jobs, BENGALURU) == []
