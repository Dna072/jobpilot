"""Sweden-first geography for scout and matching.

Priority cities are Uppsala, Stockholm, Gothenburg, and Malmö.
Other Swedish locations come next, then the rest of the EU.
US-only / non-EU onsite roles are out of scope.
"""

from __future__ import annotations

from jobpilot.schemas.common import WorkMode

SWEDEN_PRIORITY_CITIES = {
    "uppsala": 1.0,
    "stockholm": 1.0,
    "gothenburg": 1.0,
    "göteborg": 1.0,
    "goteborg": 1.0,
    "malmö": 1.0,
    "malmo": 1.0,
}

SWEDEN_ALIASES = {
    "sweden",
    "sverige",
    "swedish",
    "stockholm",
    "uppsala",
    "gothenburg",
    "göteborg",
    "goteborg",
    "malmö",
    "malmo",
}

NORDIC = {"sweden", "sverige", "denmark", "norway", "finland", "iceland"}
EUROPE = NORDIC | {
    "germany",
    "netherlands",
    "switzerland",
    "ireland",
    "belgium",
    "austria",
    "france",
    "spain",
    "italy",
    "portugal",
    "poland",
    "estonia",
    "latvia",
    "lithuania",
    "czech republic",
    "czechia",
    "europe",
    "eu",
    "emea",
    "european union",
}

OUT_OF_SCOPE = {
    "united states",
    "usa",
    "u.s.",
    "us-only",
    "canada",
    "india",
    "brazil",
    "mexico",
    "australia",
    "singapore",
    "japan",
    "china",
}

JOBTECH_PRIORITY_MUNICIPALITIES = {
    "0380": "Uppsala",
    "0180": "Stockholm",
    "1480": "Göteborg",
    "1280": "Malmö",
}


def location_blob(*parts: str | None) -> str:
    return " ".join(p for p in parts if p).lower()


def is_sweden_priority_city(blob: str) -> bool:
    return any(city in blob for city in SWEDEN_PRIORITY_CITIES)


def is_sweden(blob: str) -> bool:
    return any(alias in blob for alias in SWEDEN_ALIASES)


def is_europe(blob: str) -> bool:
    return any(name in blob for name in EUROPE)


def is_explicitly_out_of_scope(blob: str, work_mode: WorkMode | str | None = None) -> bool:
    mode = work_mode.value if isinstance(work_mode, WorkMode) else (work_mode or "")
    remote = "remote" in f"{blob} {mode}".lower()
    if is_sweden(blob) or is_europe(blob):
        return False
    if any(token in blob for token in OUT_OF_SCOPE):
        if remote and ("europe" in blob or "eu" in blob or "emea" in blob):
            return False
        return True
    return False


def in_geographic_scope(
    location: str = "",
    country: str | None = None,
    city: str | None = None,
    work_mode: WorkMode | str | None = None,
) -> bool:
    blob = location_blob(location, country, city)
    if is_explicitly_out_of_scope(blob, work_mode):
        return False
    if not blob.strip():
        return True
    if is_sweden(blob) or is_europe(blob):
        return True
    mode = work_mode.value if isinstance(work_mode, WorkMode) else (work_mode or "")
    if "remote" in f"{blob} {mode}".lower() and (
        "europe" in blob or "eu" in blob or "emea" in blob or "worldwide" in blob
    ):
        return True
    return False


def location_rank(
    location: str = "",
    country: str | None = None,
    city: str | None = None,
    work_mode: WorkMode | str | None = None,
) -> float:
    """Higher is better. Used to sort scout results and pending applications."""
    if not in_geographic_scope(location, country, city, work_mode):
        return 0.0
    blob = location_blob(location, country, city)
    if is_sweden_priority_city(blob):
        return 1.0
    if is_sweden(blob):
        return 0.86
    if any(name in blob for name in ("denmark", "norway", "finland")):
        return 0.78
    if is_europe(blob):
        return 0.62
    mode = work_mode.value if isinstance(work_mode, WorkMode) else (work_mode or "")
    if "remote" in f"{blob} {mode}".lower():
        return 0.55
    return 0.35


def location_match_score(
    location: str = "",
    country: str | None = None,
    city: str | None = None,
    work_mode: WorkMode | str | None = None,
    config: dict | None = None,
) -> float:
    """0–1 score for the match rubric. Priority cities always win over country weights."""
    blob = location_blob(location, country, city, getattr(work_mode, "value", work_mode) or "")
    cities = (config or {}).get("priority_cities") or SWEDEN_PRIORITY_CITIES
    for name, weight in cities.items():
        if str(name).lower() in blob:
            return float(weight)
    countries = (config or {}).get("priority_countries") or {"Sweden": 0.86}
    for name, weight in countries.items():
        if str(name).lower() in blob:
            return float(weight)
    return location_rank(location, country, city, work_mode)
