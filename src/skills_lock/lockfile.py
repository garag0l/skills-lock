"""Read, write and describe the skills-lock lockfile schema."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from . import __version__

SCHEMA_VERSION = 1
DEFAULT_LOCKFILE = "skills-lock.json"


def build_lockfile(skills: dict[str, dict[str, object]]) -> dict[str, object]:
    """Build the in-memory lockfile document from scanned skills."""
    skills_out: dict[str, dict[str, object]] = {}
    for name in sorted(skills):
        s = skills[name]
        skills_out[name] = {
            "path": s["path"],
            "file_count": s["file_count"],
            "skill_hash": s["skill_hash"],
            "files": dict(sorted(s["files"].items())),  # type: ignore[arg-type]
        }
    return {
        "schema_version": SCHEMA_VERSION,
        "tool_version": __version__,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "skills": skills_out,
    }


def write_lockfile(doc: dict[str, object], path: Path) -> None:
    """Write the lockfile document as deterministic, pretty JSON."""
    path = Path(path)
    text = json.dumps(doc, indent=2, sort_keys=True, ensure_ascii=False)
    path.write_text(text + "\n", encoding="utf-8")


def read_lockfile(path: Path) -> dict[str, object]:
    """Read and minimally validate a lockfile document.

    Raises FileNotFoundError if the file is missing and ValueError if the
    content is not a valid lockfile.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"lockfile not found: {path}")
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"lockfile is not valid JSON: {exc}") from exc
    if not isinstance(doc, dict) or "skills" not in doc or "schema_version" not in doc:
        raise ValueError("lockfile is missing required keys")
    if not isinstance(doc["skills"], dict):
        raise ValueError("lockfile 'skills' must be an object")
    return doc


def lockfile_skills(doc: dict[str, object]) -> dict[str, dict[str, object]]:
    """Return the ``skills`` mapping from a lockfile document."""
    skills = doc.get("skills", {})
    if not isinstance(skills, dict):
        return {}
    return skills  # type: ignore[return-value]


def default_skills_dirs() -> list[Path]:
    """Return the default skills directories to scan."""
    return [Path.home() / ".claude" / "skills"]
