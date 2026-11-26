"""End-to-end CLI tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from skills_lock.cli import main


def test_version(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "0.1.0" in out


def test_lock_then_verify_clean(skills_dir: Path, tmp_path: Path, capsys):
    lock = tmp_path / "skills-lock.json"
    rc = main(["lock", "--skills-dir", str(skills_dir), "-o", str(lock)])
    assert rc == 0
    assert lock.exists()
    capsys.readouterr()

    rc = main(["verify", "--skills-dir", str(skills_dir), "-l", str(lock)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "no drift" in out.lower()


def test_verify_detects_modification(skills_dir: Path, tmp_path: Path, capsys):
    lock = tmp_path / "skills-lock.json"
    main(["lock", "--skills-dir", str(skills_dir), "-o", str(lock)])
    capsys.readouterr()

    (skills_dir / "alpha" / "SKILL.md").write_text("# hacked\n", encoding="utf-8")

    rc = main(["verify", "--skills-dir", str(skills_dir), "-l", str(lock)])
    assert rc == 1
    out = capsys.readouterr().out
    assert "alpha" in out
    assert "modified" in out.lower()


def test_verify_json_output_parses(skills_dir: Path, tmp_path: Path, capsys):
    lock = tmp_path / "skills-lock.json"
    main(["lock", "--skills-dir", str(skills_dir), "-o", str(lock)])
    capsys.readouterr()

    (skills_dir / "alpha" / "extra.txt").write_text("x\n", encoding="utf-8")

    rc = main(
        ["verify", "--skills-dir", str(skills_dir), "-l", str(lock), "-f", "json"]
    )
    assert rc == 1
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["has_drift"] is True
    assert set(data) >= {
        "has_drift",
        "new_skills",
        "missing_skills",
        "changed_skills",
    }
    assert data["changed_skills"][0]["name"] == "alpha"
    assert data["changed_skills"][0]["added"] == ["extra.txt"]


def test_status_json(skills_dir: Path, capsys):
    rc = main(["status", "--skills-dir", str(skills_dir), "-f", "json"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert data["skill_count"] == 2
    assert set(data["skills"]) == {"alpha", "beta"}


def test_diff_always_exits_zero(skills_dir: Path, tmp_path: Path, capsys):
    lock = tmp_path / "skills-lock.json"
    main(["lock", "--skills-dir", str(skills_dir), "-o", str(lock)])
    capsys.readouterr()

    (skills_dir / "alpha" / "SKILL.md").write_text("# changed\n", encoding="utf-8")
    rc = main(["diff", "--skills-dir", str(skills_dir), "-l", str(lock)])
    assert rc == 0  # diff is informational only


def test_verify_missing_lockfile_errors(skills_dir: Path, tmp_path: Path, capsys):
    rc = main(
        ["verify", "--skills-dir", str(skills_dir), "-l", str(tmp_path / "x.json")]
    )
    assert rc == 2
    err = capsys.readouterr().err
    assert "error" in err.lower()


def test_lock_json_lockfile_has_expected_structure(skills_dir: Path, tmp_path: Path):
    lock = tmp_path / "skills-lock.json"
    main(["lock", "--skills-dir", str(skills_dir), "-o", str(lock)])
    doc = json.loads(lock.read_text(encoding="utf-8"))
    assert doc["schema_version"] == 1
    assert doc["skills"]["alpha"]["file_count"] == 2
    assert "skill_hash" in doc["skills"]["alpha"]
    assert "SKILL.md" in doc["skills"]["alpha"]["files"]
