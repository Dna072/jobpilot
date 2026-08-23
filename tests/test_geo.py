from jobpilot.geo import in_geographic_scope, location_rank, location_match_score
from jobpilot.schemas.common import WorkMode
from jobpilot.sources.jobtech import posting_from_jobtech


def test_priority_swedish_cities_outrank_other_eu():
    uppsala = location_rank("Uppsala, Sweden", "Sweden", "Uppsala")
    stockholm = location_rank("Stockholm, Sweden", "Sweden", "Stockholm")
    gothenburg = location_rank("Gothenburg, Sweden", "Sweden", "Gothenburg")
    malmo = location_rank("Malmö, Sweden", "Sweden", "Malmö")
    berlin = location_rank("Berlin, Germany", "Germany", "Berlin")
    assert uppsala == stockholm == gothenburg == malmo == 1.0
    assert berlin < uppsala


def test_us_onsite_out_of_scope():
    assert not in_geographic_scope("New York, USA", "United States", "New York", WorkMode.ONSITE)
    assert location_rank("New York, USA", "United States", "New York", WorkMode.ONSITE) == 0.0


def test_remote_europe_in_scope():
    assert in_geographic_scope("Remote, Europe", "Europe", None, WorkMode.REMOTE)


def test_location_match_uses_priority_cities():
    score = location_match_score("Uppsala", "Sweden", "Uppsala", WorkMode.HYBRID)
    assert score == 1.0


def test_jobtech_parser_maps_platsbanken_hit():
    posting = posting_from_jobtech(
        {
            "id": "31323415",
            "headline": "Data engineer",
            "webpage_url": "https://arbetsformedlingen.se/platsbanken/annonser/31323415",
            "publication_date": "2026-08-06T00:00:07",
            "application_deadline": "2026-08-27T23:59:59",
            "description": {"text": "Python SQL pipelines in Stockholm"},
            "employer": {"name": "UTBETALNINGSMYNDIGHETEN"},
            "application_details": {"url": "https://example.se/apply"},
            "workplace_address": {
                "municipality": "Stockholm",
                "city": "Stockholm",
                "country": "Sverige",
            },
        }
    )
    assert posting.source == "jobtech"
    assert posting.company == "UTBETALNINGSMYNDIGHETEN"
    assert posting.country == "Sweden"
    assert posting.city == "Stockholm"
    assert posting.job_url == "https://example.se/apply"
