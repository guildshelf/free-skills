# Secrets Sweeper Lite

Offline scan for the **10 most dangerous hardcoded credential types** before
you publish, open-source, or hand off a directory. Private key blocks, AWS
access keys, GitHub tokens, OpenAI / Anthropic / Google API keys, Slack
tokens, Stripe live keys, JWTs, and generic `key/secret/token = "..."`
assignments (entropy-checked).

- **One file, stdlib only** — `scripts/sweeper_lite.py`, Python 3.9+, no pip
  installs.
- **Zero network calls** — nothing you scan leaves your machine.
- **Masked output** — findings never contain the full secret (first 4 + last
  2 characters kept), so terminal output is safe to share.
- **CI-friendly** — exit `0` clean, `1` findings, `2` error.

## Quick start

```
python scripts/sweeper_lite.py path/to/your/repo
```

Example output:

```
CRITICAL src/config.py:14:9 anthropic-key  sk-a**********************99
HIGH     deploy/notes.md:3:1 jwt            eyJh*******************.q1
scanned 214 files (skipped 6) | findings: 2 (critical: 1, high: 1)
FAIL: rotate every CRITICAL credential at its provider first, replace with
environment variables, then re-scan to zero.
```

## Use as an agent skill

Drop this folder into your agent's skills directory (for Claude Code:
`~/.claude/skills/secrets-sweeper-lite/`). The `SKILL.md` frontmatter handles
triggering; the agent runs the script and walks you through remediation.

## What the Lite edition deliberately leaves out

Honest scope: this edition covers **credentials only**, prints to the
terminal, and has no config surface. The full Secrets Hygiene Sweeper adds
~30 more rules (emails, phones, IPs, tunnel domains, personal paths), custom
denylists for names/internal terms, masked Markdown + JSON report export,
`.sweeperignore` + inline pragmas, `--fail-on` severity gating, and
per-provider remediation guides.

## License

Apache License 2.0 — see `LICENSE.txt`. Not affiliated with Anthropic;
Claude is a trademark of Anthropic, referenced only to describe
compatibility.

---

Full version — the complete Secrets Hygiene Sweeper with PII rules,
denylists, and exportable reports — is part of the Guildshelf library at
https://guildshelf.com
