"""Requested locations must outrank same-country and unplaced postings."""

from app.services.location_match import (
    MATCH_COUNTRY,
    MATCH_EXACT,
    MATCH_MISMATCH,
    MATCH_UNKNOWN,
    describe,
    match_location,
    match_rank,
)

INDIA = [{"label": "India", "city": "", "state": "", "country": "India"}]
BENGALURU = [
    {
        "label": "Bengaluru, India",
        "city": "Bengaluru",
        "state": "",
        "country": "India",
    }
]
BARE_CITY = [{"label": "Bengaluru", "city": "", "state": "", "country": ""}]


class TestPlaceInsideAToken:
    def test_finds_the_city_glued_to_an_office_name(self):
        # "Junglee Bangalore" used to resolve to nothing and read as a mismatch.
        assert "cc:IN" in describe("Junglee Bangalore")
        assert match_location("Junglee Bangalore", False, INDIA) == MATCH_EXACT

    def test_finds_the_city_before_a_suffix(self):
        assert match_location("Bangalore Office", False, BENGALURU) == MATCH_EXACT

    def test_unresolvable_token_stays_unknown(self):
        assert match_location("Head Office", False, INDIA) == MATCH_UNKNOWN


class TestCityVersusCountryPrecision:
    def test_requested_city_is_an_exact_match(self):
        assert (
            match_location("Bengaluru, Karnataka, India", False, BENGALURU)
            == MATCH_EXACT
        )

    def test_other_city_in_that_country_ranks_below(self):
        # Selecting Bengaluru should not call Chennai an equal match.
        assert match_location("Chennai", False, BENGALURU) == MATCH_COUNTRY
        assert match_location("Mumbai, MH, in", False, BARE_CITY) == MATCH_COUNTRY

    def test_requesting_a_country_matches_any_city_in_it(self):
        assert match_location("Chennai", False, INDIA) == MATCH_EXACT
        assert match_location("Gurugram,India", False, INDIA) == MATCH_EXACT

    def test_other_country_is_still_a_mismatch(self):
        assert match_location("Berlin, Germany", False, BENGALURU) == MATCH_MISMATCH
        assert match_location("Redmond, WA, us", False, INDIA) == MATCH_MISMATCH


class TestAccentedPlaceNames:
    SWEDEN = [{"label": "Sweden", "city": "", "state": "", "country": "Sweden"}]

    def test_accented_city_resolves(self):
        # "Malmö" was unindexed, so Swedish jobs read as unknown and floated
        # above genuine mismatches.
        assert match_location("Malmö", False, self.SWEDEN) == MATCH_EXACT
        assert match_location("Malmo", False, self.SWEDEN) == MATCH_EXACT

    def test_accented_city_elsewhere_is_a_mismatch(self):
        assert match_location("Malmö", False, INDIA) == MATCH_MISMATCH


class TestMatchRank:
    def test_orders_best_to_worst(self):
        verdicts = [MATCH_MISMATCH, MATCH_UNKNOWN, MATCH_COUNTRY, MATCH_EXACT]
        assert sorted(verdicts, key=match_rank) == [
            MATCH_EXACT,
            MATCH_COUNTRY,
            MATCH_UNKNOWN,
            MATCH_MISMATCH,
        ]


class TestSearchOrdersByLocation:
    def test_matched_locations_come_first(self, monkeypatch):
        from app.services import job_search_service as svc

        def fake_search_one(query, max_results, date_posted="month"):
            return (
                [
                    {
                        "title": "Backend Engineer, Payments",
                        "href": "https://jobs.lever.co/acme/berlin",
                        "body": "Location: Berlin, Germany",
                    },
                    {
                        "title": "Backend Engineer, Search",
                        "href": "https://jobs.lever.co/acme/blr",
                        "body": "Location: Bengaluru, India",
                    },
                    {
                        "title": "Backend Engineer, Growth",
                        "href": "https://jobs.lever.co/acme/chennai",
                        "body": "Location: Chennai, India",
                    },
                ],
                "google:serper",
            )

        monkeypatch.setattr(svc, "_search_one", fake_search_one)
        monkeypatch.setattr(svc, "verify_jobs", lambda jobs, **kw: (jobs, 0))

        result = svc.search_jobs(
            role="Backend Engineer",
            location="Bengaluru",
            sources=["lever"],
            location_filters=BENGALURU,
        )

        order = [job["location_match"] for job in result["jobs"]]
        assert order == sorted(order, key=match_rank)
        assert result["jobs"][0]["url"].endswith("/blr")
        # Nothing is dropped — the Berlin posting is last, not missing.
        assert any(job["url"].endswith("/berlin") for job in result["jobs"])
