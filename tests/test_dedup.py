from jobpilot.dedup import job_fingerprint, normalize_company, normalize_title


def test_normalize_title_strips_seniority():
    assert normalize_title("Senior Data Engineer") == normalize_title("Data Engineer")
    assert normalize_title("Sr. Backend Engineer") == "backend engineer"


def test_fingerprint_dedups_same_job():
    a = job_fingerprint("Klarna AB", "Senior Data Engineer", "Stockholm, Sweden", "https://x.com/job?x=1")
    b = job_fingerprint("Klarna", "Data Engineer", "Stockholm Sweden", "https://x.com/job")
    assert a == b


def test_fingerprint_differs_for_different_roles():
    a = job_fingerprint("Spotify", "Data Engineer", "Stockholm", "https://a")
    b = job_fingerprint("Spotify", "Frontend Engineer", "Stockholm", "https://b")
    assert a != b


def test_company_suffix():
    assert normalize_company("Klarna AB") == normalize_company("Klarna")
