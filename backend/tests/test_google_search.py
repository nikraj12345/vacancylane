"""Google providers must feed organic hits into the same shape DDGS uses."""

from app.services import google_search as gs


class TestGoogleAvailability:
    def test_reports_serper_when_key_present(self, monkeypatch):
        monkeypatch.setattr(gs.settings, "serper_api_key", "sk-test")
        monkeypatch.setattr(gs.settings, "google_api_key", "")
        monkeypatch.setattr(gs.settings, "google_search_engine_id", "")
        assert gs.google_search_available()
        assert gs.google_providers_configured() == ["serper"]

    def test_reports_cse_when_both_keys_present(self, monkeypatch):
        monkeypatch.setattr(gs.settings, "serper_api_key", "")
        monkeypatch.setattr(gs.settings, "google_api_key", "gkey")
        monkeypatch.setattr(gs.settings, "google_search_engine_id", "cx")
        assert gs.google_providers_configured() == ["google_cse"]

    def test_disabled_without_keys(self, monkeypatch):
        monkeypatch.setattr(gs.settings, "serper_api_key", "")
        monkeypatch.setattr(gs.settings, "google_api_key", "")
        monkeypatch.setattr(gs.settings, "google_search_engine_id", "")
        assert not gs.google_search_available()


class TestSerperSearch:
    def test_parses_organic_results(self, monkeypatch):
        monkeypatch.setattr(gs.settings, "serper_api_key", "sk-test")
        monkeypatch.setattr(gs.settings, "google_api_key", "")
        monkeypatch.setattr(gs.settings, "google_search_engine_id", "")

        class FakeResponse:
            status_code = 200

            def raise_for_status(self):
                return None

            def json(self):
                return {
                    "organic": [
                        {
                            "title": "Backend Engineer",
                            "link": "https://jobs.lever.co/acme/1",
                            "snippet": "Remote role",
                        },
                        {
                            "title": "Backend Engineer II",
                            "link": "https://jobs.lever.co/acme/2",
                            "snippet": "Bangalore",
                        },
                    ]
                }

        class FakeClient:
            def __init__(self, *args, **kwargs):
                pass

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def post(self, url, headers=None, json=None):
                assert url == gs.SERPER_URL
                assert headers["X-API-KEY"] == "sk-test"
                assert json["q"]
                return FakeResponse()

        monkeypatch.setattr(gs.httpx, "Client", FakeClient)
        results, provider = gs.search_google("site:jobs.lever.co Backend", 10)
        assert provider == "google:serper"
        assert len(results) == 2
        assert results[0]["href"].endswith("/1")
        assert results[0]["body"] == "Remote role"

    def test_returns_empty_without_keys(self, monkeypatch):
        monkeypatch.setattr(gs.settings, "serper_api_key", "")
        monkeypatch.setattr(gs.settings, "google_api_key", "")
        monkeypatch.setattr(gs.settings, "google_search_engine_id", "")
        results, provider = gs.search_google("anything", 5)
        assert results == []
        assert provider == "none"


class TestSearchOneUsesGoogle:
    def test_prefers_google_hits_over_ddgs(self, monkeypatch):
        from app.services import job_search_service as svc

        monkeypatch.setattr(svc, "google_search_available", lambda: True)

        def fake_google(query, max_results=20, date_posted="month"):
            hits = [
                {
                    "title": f"Backend {i}",
                    "href": f"https://jobs.lever.co/acme/g{i}",
                    "body": "from google",
                }
                for i in range(12)
            ]
            return hits, "google:serper"

        monkeypatch.setattr(svc, "search_google", fake_google)

        class ShouldNotCall:
            def __init__(self, *args, **kwargs):
                raise AssertionError("DDGS should be skipped when Google is full")

        monkeypatch.setattr(svc, "DDGS", ShouldNotCall)
        results, provider = svc._search_one("site:jobs.lever.co Backend", 20)
        assert provider == "google:serper"
        assert len(results) == 12
