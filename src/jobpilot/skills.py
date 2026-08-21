from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

from jobpilot.config import repo_path

TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9+.#/-]{1,}")


@lru_cache
def load_taxonomy() -> dict:
    path = repo_path("data", "skill_taxonomy.yaml")
    import yaml

    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def canonical_skill(raw: str) -> str:
    tax = load_taxonomy()
    needle = raw.strip().lower()
    aliases: dict[str, list[str]] = tax.get("aliases", {})
    if needle in aliases:
        return needle
    for canonical, names in aliases.items():
        if needle == canonical or needle in [n.lower() for n in names]:
            return canonical
    return needle


def expand_aliases(skill: str) -> set[str]:
    tax = load_taxonomy()
    skill = canonical_skill(skill)
    names = {skill}
    for extra in tax.get("aliases", {}).get(skill, []):
        names.add(extra.lower())
    names.add(skill.replace(".", "").replace("-", " "))
    return {n.lower() for n in names}


def candidate_skill_set(profile: dict) -> set[str]:
    skills = set()
    block = profile.get("skills", {})
    for key, values in block.items():
        if key == "brief_only_do_not_claim_as_employment":
            continue
        if key == "explicit_gaps":
            continue
        for item in values:
            skills.add(canonical_skill(item))
    for exp in profile.get("experience", []):
        for item in exp.get("skills", []):
            skills.add(canonical_skill(item))
    return skills


def extract_skills_from_text(text: str) -> list[str]:
    tax = load_taxonomy()
    blob = (text or "").lower()
    found: list[str] = []
    seen: set[str] = set()
    catalog: list[str] = []
    for names in tax.get("categories", {}).values():
        catalog.extend(names)
    catalog.extend(tax.get("aliases", {}).keys())
    catalog = sorted(set(catalog), key=len, reverse=True)
    for name in catalog:
        variants = expand_aliases(name) | {name.lower()}
        if any(re.search(rf"(?<![a-z0-9]){re.escape(v)}(?![a-z0-9])", blob) for v in variants if v):
            canon = canonical_skill(name)
            if canon not in seen:
                seen.add(canon)
                found.append(canon)
    return found


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
