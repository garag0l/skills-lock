"""Shared pytest fixtures: a fake skills tree."""

from __future__ import annotations

from pathlib import Path

import pytest


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


@pytest.fixture
def skills_dir(tmp_path: Path) -> Path:
    """Create a skills root containing two skills, each SKILL.md + a helper."""
    root = tmp_path / "skills"

    _write(root / "alpha" / "SKILL.md", "# Alpha skill\nDo alpha things.\n")
    _write(root / "alpha" / "helper.py", "def alpha():\n    return 1\n")

    _write(root / "beta" / "SKILL.md", "# Beta skill\nDo beta things.\n")
    _write(root / "beta" / "scripts" / "run.sh", "#!/bin/sh\necho beta\n")

    return root
