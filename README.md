# skills-lock

A lockfile and tamper/drift detector for installed AI agent **skills** (Claude
Code / Codex agent skills).

## What it is

Agent skills are directories — each usually a `SKILL.md` plus supporting files —
installed under locations like `~/.claude/skills/` and plugin skill
directories. Because a skill's text becomes **instructions the agent follows**,
a silent change to an installed skill is a supply-chain and tampering risk: an
edited skill can quietly redirect what your agent does.

`skills-lock` pins the content of your installed skills and makes any later
change detectable — think `package-lock.json` or pip hashes, but for agent
skills. It computes a SHA-256 for every file and a deterministic skill-level
hash, records them in a lockfile, and then tells you exactly what changed.

- **Zero third-party runtime dependencies.** Standard library only.
- **Python 3.9+**, cross-platform and deterministic.

## Install

```bash
pip install skills-lock
```

Or from source:

```bash
pip install .
# for development (tests + linter):
pip install -e ".[dev]"
```

## Usage

### `skills-lock lock`

Scan each skills directory and write a lockfile.

```bash
skills-lock lock
# Wrote skills-lock.json (3 skills).

# custom locations and output path:
skills-lock lock --skills-dir ~/.claude/skills --skills-dir ./plugin/skills -o skills-lock.json
```

By default it scans `~/.claude/skills`. Pass `--skills-dir` (repeatable) to scan
other roots, including plugin skill directories.

### `skills-lock verify`

Re-scan and compare against the lockfile. **Exits non-zero (1) if any drift is
found**, 0 if clean — suitable for CI or a pre-run guard.

```bash
skills-lock verify
# OK: no drift detected; all skills match the lockfile.

skills-lock verify
# Drift detected:
#   ~ changed skill: pdf
#       modified: SKILL.md
#       added:    helper.py
#   - missing skill: morning
#   + new skill:     rogue-skill
```

JSON output for tooling:

```bash
skills-lock verify -f json
```

```json
{
  "changed_skills": [
    {
      "added": ["helper.py"],
      "modified": ["SKILL.md"],
      "name": "pdf",
      "removed": []
    }
  ],
  "has_drift": true,
  "missing_skills": ["morning"],
  "new_skills": ["rogue-skill"]
}
```

### `skills-lock status`

Summarize the skills currently installed (no lockfile needed).

```bash
skills-lock status
# Skills found: 3
#   morning  (4 files, 1a2b3c4d5e6f)
#   pdf      (7 files, 0f9e8d7c6b5a)
#   skill-creator  (12 files, abcdef012345)
```

### `skills-lock diff`

Same comparison as `verify`, but always exits 0 — for an informational
current-vs-lock summary.

### Global options

- `-f, --format {text,json}` — output format (default: `text`).
- `--no-color` — disable ANSI color in text output.
- `-V, --version` — print version.
- `-l, --lockfile FILE` — lockfile path for `verify` / `diff`
  (default: `skills-lock.json`).

## Lockfile schema

The lockfile is deterministic, pretty-printed, key-sorted JSON:

```json
{
  "schema_version": 1,
  "tool_version": "0.1.0",
  "generated_at": "2026-11-26T00:00:00Z",
  "skills": {
    "pdf": {
      "path": ".../.claude/skills/pdf",
      "file_count": 2,
      "skill_hash": "<sha256 over sorted (relpath, filehash) pairs>",
      "files": {
        "SKILL.md": "<sha256>",
        "scripts/convert.py": "<sha256>"
      }
    }
  }
}
```

- Paths inside the lockfile always use `/` separators so the file is portable
  across Windows, macOS and Linux.
- `skill_hash` is computed over the sorted `relative-path` + `file-hash` pairs,
  so it is independent of filesystem traversal order and of the skill's absolute
  location.
- Unreadable files are reported as warnings on stderr and simply omitted from
  the hashes, rather than crashing the scan. Binary files are hashed as raw
  bytes.

## Authorized use only

`skills-lock` is a **defensive** integrity tool. Use it only on skills and
systems that you own or administer, or where you have explicit authorization.
It reads files under the skills directories you point it at and never modifies,
exfiltrates or transmits their content — all hashing is local. Do not use it to
inspect or monitor systems you are not authorized to access.

## License

MIT © Murat Bekgi. See [LICENSE](LICENSE).
