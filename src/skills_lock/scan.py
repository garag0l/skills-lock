"""Walk skill directories and compute deterministic content hashes."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

# Size of the chunk used when reading files for hashing.
_CHUNK = 65536


def _hash_file(path: Path) -> str:
    """Return the SHA-256 hex digest of a file's bytes.

    Raises OSError (including PermissionError) if the file cannot be read; the
    caller is responsible for reporting that without crashing the whole scan.
    """
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(_CHUNK), b""):
            h.update(chunk)
    return h.hexdigest()


def _normalize(rel: Path) -> str:
    """Normalize a relative path to a deterministic, cross-platform string."""
    return rel.as_posix()


def scan_skill(skill_dir: Path) -> dict[str, object]:
    """Scan a single skill directory.

    Returns a dict with:
      - ``path``: the skill directory as given (string, normalized separators)
      - ``name``: the skill directory's base name
      - ``file_count``: number of files successfully hashed
      - ``files``: {relative-posix-path: sha256-hex} sorted by key
      - ``errors``: {relative-posix-path: message} for unreadable files
      - ``skill_hash``: deterministic hash over sorted (path, filehash) pairs
    """
    skill_dir = Path(skill_dir)
    files: dict[str, str] = {}
    errors: dict[str, str] = {}

    for root, dirnames, filenames in os.walk(skill_dir):
        # Sort in place so traversal order is deterministic.
        dirnames.sort()
        for fname in sorted(filenames):
            abs_path = Path(root) / fname
            rel = _normalize(abs_path.relative_to(skill_dir))
            try:
                files[rel] = _hash_file(abs_path)
            except OSError as exc:
                errors[rel] = f"{type(exc).__name__}: {exc}"

    skill_hash = compute_skill_hash(files)

    return {
        "path": skill_dir.as_posix(),
        "name": skill_dir.name,
        "file_count": len(files),
        "files": dict(sorted(files.items())),
        "errors": dict(sorted(errors.items())),
        "skill_hash": skill_hash,
    }


def compute_skill_hash(files: dict[str, str]) -> str:
    """Compute a deterministic skill-level hash from per-file hashes.

    The hash is SHA-256 over the sorted ``relpath\\0filehash\\n`` records, so it
    is stable regardless of filesystem traversal order and independent of the
    absolute location of the skill directory.
    """
    h = hashlib.sha256()
    for rel, filehash in sorted(files.items()):
        h.update(rel.encode("utf-8"))
        h.update(b"\x00")
        h.update(filehash.encode("utf-8"))
        h.update(b"\n")
    return h.hexdigest()


def _iter_skill_dirs(skills_dir: Path) -> list[Path]:
    """Return immediate sub-directories of ``skills_dir`` that are skills.

    A skill is any immediate child directory. Missing or non-directory inputs
    yield an empty list rather than raising.
    """
    if not skills_dir.is_dir():
        return []
    return sorted(
        (child for child in skills_dir.iterdir() if child.is_dir()),
        key=lambda p: p.name,
    )


def scan_dirs(skills_dirs: list[Path]) -> dict[str, dict[str, object]]:
    """Scan one or more skills roots.

    Returns a mapping of skill *name* -> skill scan dict. When the same skill
    name appears under multiple roots, later roots win but both paths are kept
    distinct by using the name as key (first occurrence by sorted root order is
    preserved unless overwritten). Missing roots are skipped silently (the
    caller may inspect ``missing_dirs`` via :func:`scan_dirs_detailed`).
    """
    result, _ = scan_dirs_detailed(skills_dirs)
    return result


def scan_dirs_detailed(
    skills_dirs: list[Path],
) -> tuple[dict[str, dict[str, object]], list[str]]:
    """Like :func:`scan_dirs` but also return a list of missing root paths."""
    skills: dict[str, dict[str, object]] = {}
    missing: list[str] = []
    for raw in skills_dirs:
        root = Path(raw)
        if not root.is_dir():
            missing.append(root.as_posix())
            continue
        for skill_dir in _iter_skill_dirs(root):
            skills[skill_dir.name] = scan_skill(skill_dir)
    return skills, missing
