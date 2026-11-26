"""Tests for the diff engine."""

from __future__ import annotations

from pathlib import Path

from skills_lock.diff import diff_skills
from skills_lock.scan import scan_dirs_detailed


def _lock_and_current(skills_dir: Path):
    locked, _ = scan_dirs_detailed([skills_dir])
    return locked


def test_no_drift_on_unchanged_tree(skills_dir: Path):
    locked = _lock_and_current(skills_dir)
    current, _ = scan_dirs_detailed([skills_dir])
    result = diff_skills(locked, current)
    assert not result.has_drift
    assert result.changed_skills == []


def test_modified_file_detected(skills_dir: Path):
    locked = _lock_and_current(skills_dir)
    (skills_dir / "alpha" / "SKILL.md").write_text("# tampered\n", encoding="utf-8")
    current, _ = scan_dirs_detailed([skills_dir])
    result = diff_skills(locked, current)
    assert result.has_drift
    assert len(result.changed_skills) == 1
    delta = result.changed_skills[0]
    assert delta.name == "alpha"
    assert delta.modified == ["SKILL.md"]
    assert delta.added == []
    assert delta.removed == []


def test_added_file_detected(skills_dir: Path):
    locked = _lock_and_current(skills_dir)
    (skills_dir / "alpha" / "extra.txt").write_text("new\n", encoding="utf-8")
    current, _ = scan_dirs_detailed([skills_dir])
    result = diff_skills(locked, current)
    delta = result.changed_skills[0]
    assert delta.added == ["extra.txt"]


def test_removed_file_detected(skills_dir: Path):
    locked = _lock_and_current(skills_dir)
    (skills_dir / "alpha" / "helper.py").unlink()
    current, _ = scan_dirs_detailed([skills_dir])
    result = diff_skills(locked, current)
    delta = result.changed_skills[0]
    assert delta.removed == ["helper.py"]


def test_new_skill_detected(skills_dir: Path):
    locked = _lock_and_current(skills_dir)
    new_skill = skills_dir / "gamma"
    new_skill.mkdir()
    (new_skill / "SKILL.md").write_text("# gamma\n", encoding="utf-8")
    current, _ = scan_dirs_detailed([skills_dir])
    result = diff_skills(locked, current)
    assert result.new_skills == ["gamma"]
    assert result.has_drift


def test_missing_skill_detected(skills_dir: Path):
    locked = _lock_and_current(skills_dir)
    import shutil

    shutil.rmtree(skills_dir / "beta")
    current, _ = scan_dirs_detailed([skills_dir])
    result = diff_skills(locked, current)
    assert result.missing_skills == ["beta"]
    assert result.has_drift
