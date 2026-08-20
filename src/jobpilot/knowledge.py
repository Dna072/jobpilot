from __future__ import annotations

from pathlib import Path

from jobpilot.config import repo_path
from jobpilot.schemas.portfolio import PortfolioInventory, PortfolioProject
from jobpilot.skills import load_json


def load_candidate_profile(path: Path | None = None) -> dict:
    return load_json(path or repo_path("data", "candidate_profile.json"))


def load_inventory(path: Path | None = None) -> PortfolioInventory:
    raw = load_json(path or repo_path("data", "portfolio_inventory.json"))
    projects = [PortfolioProject.model_validate(p) for p in raw.get("projects", [])]
    return PortfolioInventory(
        github_username=raw.get("github_username", "Dna072"),
        projects=projects,
    )


def save_inventory(inventory: PortfolioInventory, path: Path | None = None) -> Path:
    dest = path or repo_path("data", "portfolio_inventory.json")
    dest.write_text(inventory.model_dump_json(indent=2), encoding="utf-8")
    return dest
