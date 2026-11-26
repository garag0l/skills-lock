# Changelog

All notable changes to this project are documented here. This project adheres
to [Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-11-26

### Added

- Initial release.
- `skills-lock lock` — scan skill directories and write a deterministic
  `skills-lock.json` lockfile with per-file SHA-256 and a per-skill content
  hash.
- `skills-lock verify` — re-scan and diff against the lockfile, reporting
  added / removed / modified files and new / missing skills; exits non-zero on
  drift.
- `skills-lock status` — summarize currently installed skills.
- `skills-lock diff` — human-readable current-vs-lock differences.
- Text and JSON output (`-f/--format`), `--no-color`, `-V/--version`.
- Zero third-party runtime dependencies (standard library only).
