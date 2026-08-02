"""Liveness classification must never hide a job it cannot prove is closed."""

import pytest

from app.services.job_liveness import (
    STATUS_CLOSED,
    STATUS_OPEN,
    STATUS_UNKNOWN,
    _classify_body,
    _redirected_away,
    parse_posting,
)


class TestParsePosting:
    @pytest.mark.parametrize(
        "url,expected",
        [
            (
                "https://boards.greenhouse.io/updater/jobs/6286209",
                ("updater", "6286209"),
            ),
            (
                "https://job-boards.greenhouse.io/acme/jobs/12345?gh_src=x",
                ("acme", "12345"),
            ),
            (
                "https://boards.greenhouse.io/embed/job_app?for=acme&token=999",
                ("acme", "999"),
            ),
        ],
    )
    def test_greenhouse(self, url, expected):
        assert parse_posting(url, "greenhouse") == expected

    def test_lever_and_ashby_require_uuid(self):
        uuid = "f2157261-4772-4771-9dc9-80dda84de1eb"
        assert parse_posting(f"https://jobs.lever.co/veda/{uuid}", "lever") == (
            "veda",
            uuid,
        )
        assert parse_posting("https://jobs.lever.co/veda", "lever") is None

    def test_smartrecruiters_strips_slug(self):
        url = "https://jobs.smartrecruiters.com/Netcentric/743999832522458--senior-be"
        assert parse_posting(url, "smartrecruiters") == (
            "Netcentric",
            "743999832522458",
        )

    def test_unsupported_source(self):
        assert parse_posting("https://x.myworkdayjobs.com/job/1", "workday") is None


class TestRedirectDetection:
    def test_bounce_to_board_root_is_closed(self):
        assert _redirected_away(
            "https://boards.greenhouse.io/updater/jobs/6286209",
            "https://job-boards.greenhouse.io/updater?error=true",
        )

    def test_same_posting_after_domain_change_is_not_closed(self):
        assert not _redirected_away(
            "https://boards.greenhouse.io/acme/jobs/6286209",
            "https://job-boards.greenhouse.io/acme/jobs/6286209",
        )

    def test_no_redirect(self):
        url = "https://jobs.lever.co/acme/abc-123"
        assert not _redirected_away(url, url)


class TestBodyClassification:
    def test_closed_marker(self):
        body = "<h1>This job is no longer accepting applications</h1>"
        assert _classify_body(body, "greenhouse") == STATUS_CLOSED

    def test_application_form_wins_over_stray_marker(self):
        # Boards often keep boilerplate about other closed roles on the page.
        body = "Apply for this job. Some roles are no longer available."
        assert _classify_body(body, "greenhouse") == STATUS_OPEN

    def test_ambiguous_page_stays_unknown(self):
        assert _classify_body("<html><body>Hello</body></html>", "lever") == (
            STATUS_UNKNOWN
        )

    def test_spa_shell_never_reports_open(self):
        body = "Apply for this job"
        assert _classify_body(body, "ashby") == STATUS_UNKNOWN

    def test_spa_still_detects_closed_in_inlined_json(self):
        body = '{"state":"This job posting is no longer active"}'
        assert _classify_body(body, "ashby") == STATUS_CLOSED
