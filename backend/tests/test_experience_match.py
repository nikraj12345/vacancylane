"""Experience is extracted and reported, never used to drop a posting."""

import pytest

from app.services.experience_match import (
    MATCH_EXACT,
    MATCH_MISMATCH,
    MATCH_UNKNOWN,
    experience_query_clause,
    extract_experience_range,
    match_experience,
)
from app.services.job_search_service import annotate_experience


class TestExtractExperience:
    @pytest.mark.parametrize(
        "text,expected",
        [
            ("2-5 years of experience", (2.0, 5.0)),
            ("Looking for 3 to 5 years experience", (3.0, 5.0)),
            ("Minimum 5 years of experience", (5.0, 50.0)),
            ("5+ years experience required", (5.0, 50.0)),
            ("Requires 4 years of experience", (4.0, 4.0)),
            ("Senior Backend Engineer", (5.0, 8.0)),
            ("Junior Software Engineer", (0.0, 2.0)),
            ("No mention of tenure here", None),
        ],
    )
    def test_extracts_ranges(self, text, expected):
        assert extract_experience_range(text) == expected


class TestMatchExperience:
    def test_overlap_is_a_match(self):
        assert match_experience("3-5 years experience", ["2-5"])[0] == MATCH_EXACT
        assert match_experience("5+ years", ["5-8", "8-12"])[0] == MATCH_EXACT
        assert match_experience("exactly 2 years of experience", ["0-2"])[0] == (
            MATCH_EXACT
        )

    def test_boundary_only_overlap_is_not_enough(self):
        # "Senior" maps to 5–8; sharing the year 5 with 2–5 must not count.
        assert match_experience("Senior Backend Engineer", ["2-5"])[0] == (
            MATCH_MISMATCH
        )
        assert match_experience("5+ years experience", ["2-5"])[0] == MATCH_MISMATCH

    def test_non_overlap_is_mismatch(self):
        assert match_experience("10+ years", ["0-2"])[0] == MATCH_MISMATCH
        assert match_experience("Fresher role", ["8-12"])[0] == MATCH_MISMATCH

    def test_missing_experience_is_unknown_when_bands_selected(self):
        assert match_experience("Backend Engineer", ["2-5"])[0] == MATCH_UNKNOWN

    def test_no_bands_selected_is_unknown(self):
        assert match_experience("5 years experience", [])[0] == MATCH_UNKNOWN


class TestExperienceQueryClause:
    def test_builds_or_clause(self):
        clause = experience_query_clause(["0-2", "2-5"])
        assert '"0-2 years"' in clause
        assert '"2-5 years"' in clause
        assert " OR " in clause


class TestAnnotateExperience:
    def test_labels_every_job_without_dropping_any(self):
        jobs = [
            {"title": "Engineer", "snippet": "3-4 years of experience"},
            {"title": "Engineer", "snippet": "10+ years required"},
            {"title": "Engineer", "snippet": "Great team culture"},
        ]
        annotated = annotate_experience(jobs, ["2-5"])

        assert len(annotated) == 3
        assert [job["experience_match"] for job in annotated] == [
            MATCH_EXACT,
            MATCH_MISMATCH,
            MATCH_UNKNOWN,
        ]

    def test_reports_the_extracted_range(self):
        jobs = [{"title": "Engineer", "snippet": "3-4 years of experience"}]
        assert annotate_experience(jobs, ["2-5"])[0]["experience_years"] == "3-4"

    def test_without_bands_everything_is_unknown(self):
        jobs = [{"title": "Engineer", "snippet": "10+ years required"}]
        annotated = annotate_experience(jobs, [])
        assert annotated[0]["experience_match"] == MATCH_UNKNOWN
