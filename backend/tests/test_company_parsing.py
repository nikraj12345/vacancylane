"""The employer must be read from the right part of each ATS URL shape."""

import pytest

from app.services.job_search_service import (
    _company_from_url,
    _is_job_url,
    detect_source,
)


class TestCompanyFromUrl:
    @pytest.mark.parametrize(
        "url,source,expected",
        [
            ("https://jobs.lever.co/acme/abc-123", "lever", "Acme"),
            ("https://boards.greenhouse.io/stripe/jobs/12345", "greenhouse", "Stripe"),
            ("https://jobs.ashbyhq.com/openai/uuid-1", "ashby", "Openai"),
            (
                "https://jobs.smartrecruiters.com/Vodafone/744000",
                "smartrecruiters",
                "Vodafone",
            ),
            ("https://apply.workable.com/acme-corp/j/ABC123/", "workable", "Acme Corp"),
            (
                "https://www.instahyre.com/job-12345-backend-engineer-at-acme-corp/",
                "instahyre",
                "Acme Corp",
            ),
            (
                "https://www.linkedin.com/jobs/view/1234567890",
                "linkedin",
                None,
            ),
        ],
    )
    def test_reads_company_from_first_path_segment(self, url, source, expected):
        assert _company_from_url(url, source) == expected

    @pytest.mark.parametrize(
        "url,source,expected",
        [
            # Workday paths start with a locale, so the tenant subdomain is the
            # only reliable source of the employer name.
            (
                "https://paypay.wd3.myworkdayjobs.com/en-US/PayPayJobs/job/Tokyo/BE_JR1",
                "workday",
                "Paypay",
            ),
            (
                "https://nvidia.wd5.myworkdayjobs.com/en-US/NVIDIACareers/job/India/E_JR2",
                "workday",
                "Nvidia",
            ),
            (
                "https://acme.teamtailor.com/jobs/12345-backend-engineer",
                "teamtailor",
                "Acme",
            ),
            ("https://acme.bamboohr.com/careers/123", "bamboohr", "Acme"),
        ],
    )
    def test_reads_company_from_subdomain(self, url, source, expected):
        assert _company_from_url(url, source) == expected

    def test_never_returns_a_locale_as_the_company(self):
        url = "https://x.wd1.myworkdayjobs.com/en-US/Careers/job/Pune/Backend_JR9"
        assert _company_from_url(url, "workday") != "En-Us"

    def test_ignores_bare_posting_ids(self):
        assert _company_from_url("https://boards.greenhouse.io/jobs/98765", "greenhouse") is None

    def test_returns_none_for_a_bare_host(self):
        assert _company_from_url("https://jobs.lever.co/", "lever") is None


class TestDetectSource:
    @pytest.mark.parametrize(
        "url,expected",
        [
            ("https://www.linkedin.com/jobs/view/1234567890/", "linkedin"),
            ("https://wellfound.com/jobs/291234-software-engineer", "wellfound"),
            ("https://angel.co/company/acme/jobs/1", "wellfound"),
            (
                "https://www.instahyre.com/job-12345-backend-engineer-at-acme/",
                "instahyre",
            ),
        ],
    )
    def test_board_hosts(self, url, expected):
        assert detect_source(url) == expected


class TestIsJobUrl:
    @pytest.mark.parametrize(
        "url,source,expected",
        [
            ("https://www.linkedin.com/jobs/view/1234567890", "linkedin", True),
            ("https://www.linkedin.com/jobs/", "linkedin", False),
            ("https://wellfound.com/jobs/291234-software-engineer", "wellfound", True),
            ("https://wellfound.com/role/software-engineer", "wellfound", True),
            ("https://wellfound.com/", "wellfound", False),
            (
                "https://www.instahyre.com/job-12345-backend-engineer-at-acme/",
                "instahyre",
                True,
            ),
            ("https://www.instahyre.com/", "instahyre", False),
        ],
    )
    def test_board_job_paths(self, url, source, expected):
        assert _is_job_url(url, source) is expected
