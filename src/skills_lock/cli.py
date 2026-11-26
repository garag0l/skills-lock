"""Command-line interface for skills-lock."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .diff import diff_skills
from .lockfile import (
    DEFAULT_LOCKFILE,
    build_lockfile,
    default_skills_dirs,
    lockfile_skills,
    read_lockfile,
    write_lockfile,
)
from .report import (
    render_diff_json,
    render_diff_text,
    render_status_json,
    render_status_text,
    should_use_color,
)
from .scan import scan_dirs_detailed


def _resolve_skills_dirs(values: list[str] | None) -> list[Path]:
    if values:
        return [Path(v).expanduser() for v in values]
    return default_skills_dirs()


def _emit_scan_notices(missing: list[str], errors_by_skill: dict) -> None:
    for path in missing:
        print(f"warning: skills dir not found: {path}", file=sys.stderr)
    for name, errs in errors_by_skill.items():
        for rel, msg in errs.items():
            print(f"warning: could not read {name}/{rel}: {msg}", file=sys.stderr)


def _collect_errors(skills: dict) -> dict:
    out = {}
    for name, skill in skills.items():
        errs = skill.get("errors") or {}
        if errs:
            out[name] = errs
    return out


def cmd_lock(args: argparse.Namespace) -> int:
    dirs = _resolve_skills_dirs(args.skills_dir)
    skills, missing = scan_dirs_detailed(dirs)
    _emit_scan_notices(missing, _collect_errors(skills))

    doc = build_lockfile(skills)
    out_path = Path(args.output)
    write_lockfile(doc, out_path)

    print(f"Wrote {out_path} ({len(skills)} skills).")
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    dirs = _resolve_skills_dirs(args.skills_dir)
    try:
        doc = read_lockfile(Path(args.lockfile))
    except (FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    locked = lockfile_skills(doc)
    current, missing = scan_dirs_detailed(dirs)
    _emit_scan_notices(missing, _collect_errors(current))

    result = diff_skills(locked, current)

    if args.format == "json":
        print(render_diff_json(result))
    else:
        print(render_diff_text(result, use_color=should_use_color(args.no_color)))

    return 1 if result.has_drift else 0


def cmd_status(args: argparse.Namespace) -> int:
    dirs = _resolve_skills_dirs(args.skills_dir)
    current, missing = scan_dirs_detailed(dirs)
    _emit_scan_notices(missing, _collect_errors(current))

    if args.format == "json":
        print(render_status_json(current))
    else:
        print(render_status_text(current, use_color=should_use_color(args.no_color)))
    return 0


def cmd_diff(args: argparse.Namespace) -> int:
    # diff is an alias of verify's reporting, but always exits 0 (informational).
    dirs = _resolve_skills_dirs(args.skills_dir)
    try:
        doc = read_lockfile(Path(args.lockfile))
    except (FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    locked = lockfile_skills(doc)
    current, missing = scan_dirs_detailed(dirs)
    _emit_scan_notices(missing, _collect_errors(current))

    result = diff_skills(locked, current)
    if args.format == "json":
        print(render_diff_json(result))
    else:
        print(render_diff_text(result, use_color=should_use_color(args.no_color)))
    return 0


def _add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--skills-dir",
        action="append",
        metavar="DIR",
        help="A skills root directory to scan (repeatable). "
        "Defaults to ~/.claude/skills.",
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format (default: text).",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable ANSI color in text output.",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="skills-lock",
        description="Lockfile and tamper/drift detector for installed AI agent skills.",
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    p_lock = sub.add_parser("lock", help="Scan skills and write a lockfile.")
    _add_common(p_lock)
    p_lock.add_argument(
        "-o",
        "--output",
        default=DEFAULT_LOCKFILE,
        metavar="FILE",
        help=f"Lockfile to write (default: {DEFAULT_LOCKFILE}).",
    )
    p_lock.set_defaults(func=cmd_lock)

    p_verify = sub.add_parser(
        "verify",
        help="Verify skills against the lockfile; non-zero exit on drift.",
    )
    _add_common(p_verify)
    p_verify.add_argument(
        "-l",
        "--lockfile",
        default=DEFAULT_LOCKFILE,
        metavar="FILE",
        help=f"Lockfile to read (default: {DEFAULT_LOCKFILE}).",
    )
    p_verify.set_defaults(func=cmd_verify)

    p_status = sub.add_parser("status", help="Summarize currently installed skills.")
    _add_common(p_status)
    p_status.set_defaults(func=cmd_status)

    p_diff = sub.add_parser(
        "diff", help="Show current-vs-lock differences (always exits 0)."
    )
    _add_common(p_diff)
    p_diff.add_argument(
        "-l",
        "--lockfile",
        default=DEFAULT_LOCKFILE,
        metavar="FILE",
        help=f"Lockfile to read (default: {DEFAULT_LOCKFILE}).",
    )
    p_diff.set_defaults(func=cmd_diff)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
