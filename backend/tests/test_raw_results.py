"""Raw mode must return what search found, with every filter stage disabled."""

from app.services import job_search_service as svc


class TestRawSkipsAnnotation:
    def test_raw_marks_locations_unknown_without_matching(self):
        jobs = [
            {"title": "Backend Engineer", "location": "Berlin, Germany"},
            {"title": "Backend Engineer", "location": "Tokyo, Japan"},
        ]
        filters = [{"label": "India", "city": "", "state": "", "country": "India"}]

        kept = svc.annotate_locations(jobs, filters, raw=True)

        assert len(kept) == 2
        assert all(job["location_match"] == "unknown" for job in kept)

    def test_non_raw_still_labels_the_mismatch(self):
        jobs = [
            {"title": "Backend Engineer", "location": "Berlin, Germany"},
            {"title": "Backend Engineer", "location": "Bangalore, India"},
        ]
        filters = [{"label": "India", "city": "", "state": "", "country": "India"}]

        kept = svc.annotate_locations(jobs, filters, raw=False)

        # Still two jobs: the verdict is reported, nothing is removed.
        assert len(kept) == 2
        assert kept[0]["location_match"] == "mismatch"

    def test_raw_marks_experience_unknown(self):
        jobs = [
            {"title": "Senior Backend Engineer", "snippet": "8+ years required"},
            {"title": "Junior", "snippet": "0 years"},
        ]

        kept = svc.annotate_experience(jobs, ["0-2"], raw=True)

        assert len(kept) == 2
        assert all(job["experience_match"] == "unknown" for job in kept)

    def test_non_raw_labels_experience_without_dropping(self):
        jobs = [{"title": "Senior Backend Engineer", "snippet": "8+ years required"}]

        kept = svc.annotate_experience(jobs, ["0-2"], raw=False)

        assert len(kept) == 1
        assert kept[0]["experience_match"] == "mismatch"


class TestRawSearchPipeline:
    def _fake_search(self, monkeypatch):
        """Return two hits: one real ATS job URL and one unrelated page."""

        def fake_search_one(query, max_results, date_posted="month"):
            return (
                [
                    {
                        "title": "Backend Engineer",
                        "href": "https://jobs.lever.co/acme/abc-123",
                        "body": "Location: Berlin, Germany. 10+ years experience.",
                    },
                    {
                        "title": "Our engineering blog",
                        "href": "https://example.com/blog/hiring",
                        "body": "Unrelated page",
                    },
                ],
                "google:serper",
            )

        monkeypatch.setattr(svc, "_search_one", fake_search_one)
        monkeypatch.setattr(svc, "verify_jobs", lambda jobs, **kw: (jobs, 0))

    def test_raw_keeps_non_ats_hits_and_skips_verification(self, monkeypatch):
        self._fake_search(monkeypatch)
        called = {"verify": False}

        def boom(jobs, **kwargs):
            called["verify"] = True
            return jobs, 0

        monkeypatch.setattr(svc, "verify_jobs", boom)

        result = svc.search_jobs(
            role="Backend Engineer",
            location="India",
            sources=["lever"],
            experience_bands=["0-2"],
            location_filters=[{"label": "India", "country": "India"}],
            raw_results=True,
        )

        assert result["raw_results"] is True
        assert called["verify"] is False
        assert result["removed_closed"] == 0
        urls = {job["url"] for job in result["jobs"]}
        # The unrelated page survives too: raw means no URL or relevance gate.
        assert "https://example.com/blog/hiring" in urls

    def test_filtered_mode_drops_the_same_hits(self, monkeypatch):
        self._fake_search(monkeypatch)

        result = svc.search_jobs(
            role="Backend Engineer",
            location="India",
            sources=["lever"],
            experience_bands=["0-2"],
            location_filters=[{"label": "India", "country": "India"}],
            raw_results=False,
        )

        urls = {job["url"] for job in result["jobs"]}
        assert "https://example.com/blog/hiring" not in urls

    def test_location_and_experience_never_drop_a_job(self, monkeypatch):
        """A hit outside both the requested location and band still comes back."""
        self._fake_search(monkeypatch)

        result = svc.search_jobs(
            role="Backend Engineer",
            location="India",
            sources=["lever"],
            experience_bands=["0-2"],
            location_filters=[{"label": "India", "country": "India"}],
            raw_results=False,
        )

        job = next(
            j for j in result["jobs"] if j["url"] == "https://jobs.lever.co/acme/abc-123"
        )
        # Berlin and 10+ years contradict the request, and it is kept anyway.
        assert job["location_match"] == "mismatch"
        assert job["experience_match"] == "mismatch"
