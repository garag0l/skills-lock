"""Tests for scanning and hashing."""

from __future__ import annotations

from pathlib import Path

from skills_lock.scan import compute_skill_hash, scan_dirs_detailed, scan_skill


def test_scan_skill_hashes_all_files(skills_dir: Path):
    scan = scan_skill(skills_dir / "alpha")
    assert scan["name"] == "alpha"
    assert scan["file_count"] == 2
    assert set(scan["files"]) == {"SKILL.md", "helper.py"}
    # SHA-256 hex digests are 64 chars.
    for digest in scan["files"].values():
        assert len(digest) == 64


def test_scan_uses_posix_relpaths(skills_dir: Path):
    scan = scan_skill(skills_dir / "beta")
    # Nested file must use forward slashes regardless of platform.
    assert "scripts/run.sh" in scan["files"]


def test_skill_hash_is_stable_and_order_independent():
    a = {"SKILL.md": "aa", "x/y.py": "bb"}
    b = {"x/y.py": "bb", "SKILL.md": "aa"}
    assert compute_skill_hash(a) == compute_skill_hash(b)


def test_skill_hash_changes_with_content():
    a = {"SKILL.md": "aa"}
    b = {"SKILL.md": "zz"}
    assert compute_skill_hash(a) != compute_skill_hash(b)


def test_scan_is_repeatable(skills_dir: Path):
    first = scan_skill(skills_dir / "alpha")
    second = scan_skill(skills_dir / "alpha")
    assert first["skill_hash"] == second["skill_hash"]
    assert first["files"] == second["files"]


def test_scan_dirs_detailed_finds_all_skills(skills_dir: Path):
    skills, missing = scan_dirs_detailed([skills_dir])
    assert set(skills) == {"alpha", "beta"}
    assert missing == []


def test_scan_dirs_reports_missing(tmp_path: Path):
    ghost = tmp_path / "does-not-exist"
    skills, missing = scan_dirs_detailed([ghost])
    assert skills == {}
    assert len(missing) == 1


def test_empty_skills_dir(tmp_path: Path):
    empty = tmp_path / "empty"
    empty.mkdir()
    skills, missing = scan_dirs_detailed([empty])
    assert skills == {}
    assert missing == []


def test_binary_file_is_hashed(tmp_path: Path):
    root = tmp_path / "skills"
    skill = root / "bin"
    skill.mkdir(parents=True)
    (skill / "data.bin").write_bytes(bytes(range(256)))
    scan = scan_skill(skill)
    assert scan["file_count"] == 1
    assert len(scan["files"]["data.bin"]) == 64
