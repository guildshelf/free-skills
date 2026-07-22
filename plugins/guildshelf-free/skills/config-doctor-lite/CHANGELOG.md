# Changelog

All notable changes to Config Doctor Lite are documented here.
This project adheres to [Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-07-18

### Added

- Initial open-source release of **Config Doctor Lite** (Apache-2.0), the
  free edition of the Guildshelf Config Doctor.
- `scripts/config_doctor_lite.py` — single-file, stdlib-only, 100% read-only
  scanner with 3 checks:
  - **C1** — broken backtick path references in CLAUDE.md files.
  - **C4** — skill directories missing SKILL.md.
  - **C8** — SKILL.md frontmatter missing `name`/`description`.
- Auto-discovery (`CLAUDE_CONFIG_DIR` → `~/.claude` → cwd → `--root`),
  prioritized BROKEN/ORPHANED/WEAK terminal report, per-finding fix
  suggestions.
- Exit codes `0` clean / `1` findings / `2` error.
- `SKILL.md` with triggering description (trigger + not-for cases),
  `eval/cases.md` (20 trigger / non-trigger cases), `README.md`,
  `LICENSE.txt` (Apache-2.0).

### Notes

- Lite scope: 3 of 8 checks, human-readable output only. Memory-index,
  hooks, and MCP checks plus `--json` CI output and the fix playbook are in
  the full Config Doctor.
