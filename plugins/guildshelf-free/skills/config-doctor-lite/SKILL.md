---
name: config-doctor-lite
description: >
  Quick health-check for AI coding agent configuration. Auto-discovers
  CLAUDE.md files and skill directories, then runs 3 read-only checks:
  broken path references in CLAUDE.md, skill folders missing SKILL.md, and
  weak SKILL.md frontmatter (missing name/description). Python stdlib only,
  prioritized terminal report, never writes anything. Use when the user asks
  to audit their Claude Code config, check for broken paths or dead
  references after moving/renaming a project or migrating machines, or find
  out why a skill is not loading or triggering. Not for auditing code
  dependencies (npm/pip), scanning for secrets, linting application configs
  (nginx, Docker, ESLint, Kubernetes), or creating a new CLAUDE.md from
  scratch. Memory-index, hooks, and MCP-definition checks plus JSON/CI
  output are in the full Config Doctor.
---

# Config Doctor Lite

Health-check your AI coding agent's configuration. Find broken paths in
CLAUDE.md, skill folders the agent cannot load, and frontmatter that hurts
trigger accuracy — before they silently corrupt your agent's behavior.

## When to use / when not to use

**Use this skill when:**

- The user asks to audit, health-check, or clean up their Claude Code
  configuration (CLAUDE.md, skills).
- A project folder was **moved or renamed** and references in CLAUDE.md may
  now point at nothing.
- A skill **silently stopped working** — it no longer loads or triggers, and
  nobody changed the skill itself.
- The user migrated to a new machine and wants to verify the config survived.

**Do NOT use this skill for:**

- Auditing code dependencies (npm audit, pip-audit, cargo audit).
- Scanning for secrets or hardcoded credentials (different product).
- Linting application configs: nginx, Docker/docker-compose, ESLint,
  Kubernetes, CI pipelines.
- Writing a new CLAUDE.md from scratch (this tool checks existing config;
  it does not author it).
- Checking whether web URLs are alive (only local file paths are verified).

## Quick start

Run the scanner first, then talk about the results:

```
python scripts/config_doctor_lite.py
```

The script is **100% read-only**. It never creates, modifies, or deletes
anything, so it is always safe to run. Use `--root PATH` (repeatable) for
config kept in non-standard locations.

## What gets checked (3 of the full 8)

| ID | Check | Severity |
|----|-------|----------|
| C1 | CLAUDE.md path references — every backtick path-like string must exist | BROKEN |
| C4 | Skill directory integrity — every skill subdirectory must contain SKILL.md | ORPHANED |
| C8 | SKILL.md frontmatter health — missing/empty `name` or `description` | WEAK |

## Discovery order

No paths are hardcoded. The scanner discovers config roots in this order:

1. **`CLAUDE_CONFIG_DIR`** environment variable — if set and valid, it is
   used as *the* config directory.
2. **`~/.claude/`** — on Windows: `%USERPROFILE%\.claude`. The home-level
   `~/CLAUDE.md` is also picked up here.
3. **Current working directory** — `./CLAUDE.md`, `./.claude/`.
4. **`--root PATH`** (repeatable) — add scan roots manually.

## Reading the report

- **BROKEN (must fix)** — a reference that points at nothing. The agent will
  fail, or silently skip the item, every time it hits this reference.
- **ORPHANED (should review)** — a directory that exists but is not loadable by
  the agent (skill dir without SKILL.md).
- **WEAK (informational)** — works, but hurts quality (e.g. empty skill
  description reduces trigger accuracy).

## Fix workflow (agent-guided)

The scanner never fixes anything itself. As the agent:

1. Run the scanner and present the numbered report to the user.
2. Ask which findings to fix — numbers or "all".
3. Fix one item at a time (update the reference, create a SKILL.md, add the
   missing frontmatter field).
4. **Deletion is special**: any action that deletes a file, directory, or
   config entry must be confirmed with the user *per item*. Never
   batch-delete.
5. Re-run the scanner after fixing to verify.

## Limitations

- **URLs are not verified.** Only local file paths are checked.
- **No secrets scanning.** For credential hygiene, that is a separate tool.
- **Heuristic extraction.** Backtick strings with whitespace (commands),
  wildcards, URLs, and unresolved environment variables are deliberately
  skipped to avoid false positives.
- Lite runs 3 of the full 8 checks. Memory-index integrity, orphaned memory
  files, skill-index cross-checks, hook zombie settings, and MCP-definition
  verification — plus `--json` output and CI exit-code contracts — are in
  the full **Config Doctor**.

## Disclaimer

This project is not affiliated with, endorsed by, or sponsored by Anthropic.
"Claude" is a trademark of Anthropic, PBC, used here only to describe
compatibility.
