# Config Doctor Lite

Read-only health check for your AI coding agent's configuration. Finds the
three problems that most often make an agent misbehave after a project moves
or a machine migration:

| Check | What it catches | Severity |
|---|---|---|
| C1 | Backtick path references in CLAUDE.md that point at nothing | BROKEN |
| C4 | Skill folders with no SKILL.md (the agent can't load them) | ORPHANED |
| C8 | SKILL.md frontmatter missing `name`/`description` (kills triggering) | WEAK |

- **One file, stdlib only** — `scripts/config_doctor_lite.py`, Python 3.8+.
- **100% read-only** — never creates, modifies, or deletes anything.
- **Auto-discovery** — `CLAUDE_CONFIG_DIR` → `~/.claude` → current directory,
  plus `--root` for non-standard locations. No hardcoded paths.
- Exit codes `0` clean / `1` findings / `2` error.

## Quick start

```
python scripts/config_doctor_lite.py
```

You get a prioritized report (BROKEN → ORPHANED → WEAK) with a per-finding
fix suggestion.

## Use as an agent skill

Drop this folder into your agent's skills directory (for Claude Code:
`~/.claude/skills/config-doctor-lite/`). The agent runs the scanner, walks
you through fixes one at a time, and re-runs to verify — deletions always
confirmed per item.

## What the Lite edition deliberately leaves out

Honest scope: Lite runs 3 of the full product's 8 checks and prints to the
terminal. The full Config Doctor adds memory-index integrity, orphaned
memory files, skill-index-vs-disk cross-checks, hook zombie settings, and
MCP server definition verification, plus `--json` machine output with a
stable CI field contract and a per-category fix playbook.

## License

Apache License 2.0 — see `LICENSE.txt`. Not affiliated with Anthropic;
Claude is a trademark of Anthropic, referenced only to describe
compatibility.

---

Full version — Config Doctor with all 8 checks, JSON/CI output, and the fix
playbook — is part of the Guildshelf library at https://guildshelf.com
