from __future__ import annotations

import hashlib
import re
import unicodedata

_SENIORITY = re.compile(
    r"\b(senior|sr|junior|jr|staff|principal|lead|intern|graduate|mid[- ]?level)\b",
    re.I,
)
_WS = re.compile(r"[^a-z0-9]+")


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "")
    value = value.encode("ascii", "ignore").decode("ascii")
    return _WS.sub(" ", value.lower()).strip()


def normalize_title(title: str) -> str:
    text = normalize_text(title)
    text = _SENIORITY.sub(" ", text)
    return " ".join(text.split())


def normalize_company(name: str) -> str:
    text = normalize_text(name)
    for suffix in (" ab", " gmbh", " ltd", " limited", " inc", " oy", " as", " ag", " bv"):
        if text.endswith(suffix):
            text = text[: -len(suffix)]
    return text.strip()


def job_fingerprint(company: str, title: str, location: str, url: str = "") -> str:
    key = "|".join(
        [
            normalize_company(company),
            normalize_title(title),
            normalize_text(location),
            normalize_text(url.split("?")[0]),
        ]
    )
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def source_fingerprint(source: str, source_job_id: str) -> str:
    return hashlib.sha256(f"{source}:{source_job_id}".encode()).hexdigest()
