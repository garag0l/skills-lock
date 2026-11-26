"""Tests for lockfile build/read/write."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from skills_lock.lockfile import (
    SCHEMA_VERSION,
    build_lockfile,
    lockfile_skills,
    read_lockfile,
    write_lockfile,
)
from skills_lock.scan import scan_dirs_detailed


def test_build_lockfile_has_expected_keys(skills_dir: Path):
    skills, _ = scan_dirs_detailed([skills_dir])
    doc = build_lockfile(skills)
    assert doc["schema_version"] == SCHEMA_VERSION
    assert "tool_version" in doc
    assert "generated_at" in doc
    assert set(doc["skills"]) == {"alpha", "beta"}
    alpha = doc["skills"]["alpha"]
    assert set(alpha) == {"path", "file_count", "skill_hash", "files"}


def test_write_then_read_roundtrip(skills_dir: Path, tmp_path: Path):
    skills, _ = scan_dirs_detailed([skills_dir])
    doc = build_lockfile(skills)
    out = tmp_path / "skills-lock.json"
    write_lockfile(doc, out)

    reread = read_lockfile(out)
    assert lockfile_skills(reread).keys() == lockfile_skills(doc).keys()


def test_relock_is_identical(skills_dir: Path, tmp_path: Path):
    skills, _ = scan_dirs_detailed([skills_dir])
    doc1 = build_lockfile(skills)
    skills2, _ = scan_dirs_detailed([skills_dir])
    doc2 = build_lockfile(skills2)
    # Everything except the timestamp must match exactly.
    doc1.pop("generated_at")
    doc2.pop("generated_at")
    assert doc1 == doc2


def test_read_missing_lockfile_raises(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        read_lockfile(tmp_path / "nope.json")


def test_read_invalid_json_raises(tmp_path: Path):
    bad = tmp_path / "bad.json"
    bad.write_text("not json", encoding="utf-8")
    with pytest.raises(ValueError):
        read_lockfile(bad)


def test_read_missing_keys_raises(tmp_path: Path):
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"hello": "world"}), encoding="utf-8")
    with pytest.raises(ValueError):
        read_lockfile(bad)
