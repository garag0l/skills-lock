"""Render diff and status output as text or JSON."""

from __future__ import annotations

import json
import sys

from .diff import DiffResult


class _Palette:
    """ANSI color helpers that no-op when color is disabled."""

    def __init__(self, enabled: bool) -> None:
        self.enabled = enabled

    def _wrap(self, code: str, text: str) -> str:
        if not self.enabled:
            return text
        return f"\033[{code}m{text}\033[0m"

    def red(self, text: str) -> str:
        return self._wrap("31", text)

    def green(self, text: str) -> str:
        return self._wrap("32", text)

    def yellow(self, text: str) -> str:
        return self._wrap("33", text)

    def cyan(self, text: str) -> str:
        return self._wrap("36", text)

    def bold(self, text: str) -> str:
        return self._wrap("1", text)


def should_use_color(no_color: bool) -> bool:
    """Decide whether to emit ANSI color."""
    if no_color:
        return False
    return sys.stdout.isatty()


def render_diff_text(result: DiffResult, use_color: bool = False) -> str:
    """Render a diff result as a human-readable report."""
    p = _Palette(use_color)
    lines: list[str] = []

    if not result.has_drift:
        lines.append(p.green("OK: no drift detected; all skills match the lockfile."))
        return "\n".join(lines)

    lines.append(p.bold("Drift detected:"))

    for name in result.new_skills:
        lines.append(p.yellow(f"  + new skill:     {name}"))
    for name in result.missing_skills:
        lines.append(p.red(f"  - missing skill: {name}"))

    for delta in result.changed_skills:
        lines.append(p.cyan(f"  ~ changed skill: {delta.name}"))
        for f in delta.added:
            lines.append(p.green(f"      added:    {f}"))
        for f in delta.removed:
            lines.append(p.red(f"      removed:  {f}"))
        for f in delta.modified:
            lines.append(p.yellow(f"      modified: {f}"))

    return "\n".join(lines)


def diff_to_dict(result: DiffResult) -> dict[str, object]:
    """Convert a diff result to a JSON-serializable dict."""
    return {
        "has_drift": result.has_drift,
        "new_skills": result.new_skills,
        "missing_skills": result.missing_skills,
        "changed_skills": [
            {
                "name": d.name,
                "added": d.added,
                "removed": d.removed,
                "modified": d.modified,
            }
            for d in result.changed_skills
        ],
    }


def render_diff_json(result: DiffResult) -> str:
    """Render a diff result as JSON."""
    return json.dumps(diff_to_dict(result), indent=2, sort_keys=True)


def render_status_text(
    current: dict[str, dict[str, object]], use_color: bool = False
) -> str:
    """Render a summary of the currently scanned skills."""
    p = _Palette(use_color)
    if not current:
        return p.yellow("No skills found.")
    lines = [p.bold(f"Skills found: {len(current)}")]
    for name in sorted(current):
        skill = current[name]
        count = skill.get("file_count", 0)
        shash = str(skill.get("skill_hash", ""))[:12]
        lines.append(f"  {name}  ({count} files, {shash})")
    return "\n".join(lines)


def status_to_dict(current: dict[str, dict[str, object]]) -> dict[str, object]:
    """Convert current scan state to a JSON-serializable summary dict."""
    return {
        "skill_count": len(current),
        "skills": {
            name: {
                "path": current[name].get("path"),
                "file_count": current[name].get("file_count"),
                "skill_hash": current[name].get("skill_hash"),
            }
            for name in sorted(current)
        },
    }


def render_status_json(current: dict[str, dict[str, object]]) -> str:
    """Render the current scan state as JSON."""
    return json.dumps(status_to_dict(current), indent=2, sort_keys=True)
