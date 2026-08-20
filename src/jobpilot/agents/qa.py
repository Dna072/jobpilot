from __future__ import annotations

import re
from pathlib import Path

SECRET_RE = re.compile(r"(api[_-]?key|secret|password|token)\s*=\s*['\"][^'\"]+['\"]", re.I)


def qa_project(root: Path) -> dict:
    issues: list[str] = []
    readme = root / "README.md"
    if not readme.exists():
        issues.append("Missing README.md")
    else:
        text = readme.read_text(encoding="utf-8")
        required = [
            "Project Overview",
            "Architecture",
            "Technology Choices",
            "I designed",
        ]
        for heading in required:
            if heading not in text:
                issues.append(f"README missing `{heading}`")
        if "KPMG" in text and "employment" not in text.lower() and "not" not in text.lower():
            issues.append("README may blur professional vs portfolio experience")
    if not (root / "docker-compose.yml").exists() and not (root / "Dockerfile").exists():
        issues.append("No Docker packaging")
    tests = list(root.rglob("test_*.py")) + list(root.rglob("*_test.py"))
    if not tests:
        issues.append("No tests found")
    for path in root.rglob("*"):
        if path.suffix in {".py", ".env", ".yml", ".yaml", ".json", ".ts", ".js"} and path.is_file():
            try:
                blob = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if SECRET_RE.search(blob) and ".example" not in path.name:
                issues.append(f"Possible secret in {path}")
    return {"ok": not issues, "issues": issues, "root": str(root)}
