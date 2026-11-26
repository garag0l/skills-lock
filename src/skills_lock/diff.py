"""Compare a lockfile against freshly scanned skills."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SkillDelta:
    """Per-skill file-level differences."""

    name: str
    added: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    modified: list[str] = field(default_factory=list)

    @property
    def changed(self) -> bool:
        return bool(self.added or self.removed or self.modified)


@dataclass
class DiffResult:
    """The full diff between locked and current state."""

    new_skills: list[str] = field(default_factory=list)
    missing_skills: list[str] = field(default_factory=list)
    changed_skills: list[SkillDelta] = field(default_factory=list)

    @property
    def has_drift(self) -> bool:
        return bool(self.new_skills or self.missing_skills or self.changed_skills)


def _files_of(skill: dict[str, object]) -> dict[str, str]:
    files = skill.get("files", {})
    if not isinstance(files, dict):
        return {}
    return files  # type: ignore[return-value]


def diff_skills(
    locked: dict[str, dict[str, object]],
    current: dict[str, dict[str, object]],
) -> DiffResult:
    """Diff locked skills against currently scanned skills.

    - A skill present now but not locked is a *new* skill.
    - A skill locked but absent now is a *missing* skill.
    - For skills present in both, compare per-file hashes to find added,
      removed and modified files.
    """
    result = DiffResult()

    locked_names = set(locked)
    current_names = set(current)

    result.new_skills = sorted(current_names - locked_names)
    result.missing_skills = sorted(locked_names - current_names)

    for name in sorted(locked_names & current_names):
        locked_files = _files_of(locked[name])
        current_files = _files_of(current[name])

        locked_set = set(locked_files)
        current_set = set(current_files)

        added = sorted(current_set - locked_set)
        removed = sorted(locked_set - current_set)
        modified = sorted(
            f for f in (locked_set & current_set) if locked_files[f] != current_files[f]
        )

        if added or removed or modified:
            result.changed_skills.append(
                SkillDelta(name=name, added=added, removed=removed, modified=modified)
            )

    return result
