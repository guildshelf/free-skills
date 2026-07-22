# Learn-by-Demo Lite

Build automation from **observed traffic, not guessed APIs**. The user
demonstrates a web workflow once; you capture the real network requests and
turn them into a redacted endpoint draft to build from.

Solves the classic agent failure mode: guessed endpoint → 401/403 → HTML
instead of JSON → another guess → burned iterations.

- **Methodology** — the Iron Rules and a 5-step capture workflow
  (`SKILL.md`).
- **`scripts/har_draft.py`** — stdlib-only tool: browser DevTools HAR export
  in, redacted Markdown endpoint draft out (method, URL template, auth type,
  query params, body field names, statuses). Credentials are **always**
  redacted — no off switch.
- **`fixtures/sample_capture.har`** — synthetic capture (fake tokens only)
  to practice on.

## Quick start

```
python scripts/har_draft.py fixtures/sample_capture.har
```

Then with a real capture: DevTools → Network → "Preserve log" → user
demonstrates slowly → right-click → "Save all as HAR" →
`python scripts/har_draft.py capture.har`.

## Use as an agent skill

Drop this folder into your agent's skills directory (for Claude Code:
`~/.claude/skills/learn-by-demo-lite/`). It triggers on "watch me do it
once", "no API docs", and guessed-endpoint 401/403 symptoms.

## Secrets discipline

Captures contain live credentials. The draft tool always redacts; raw HAR
files must stay out of version control and out of prompts/issues/chats.
Replay scripts read tokens from environment variables, never literals.

## What the Lite edition deliberately leaves out

Honest scope: Lite is capture (DevTools/runtime reader) + draft. The full
Learn-by-Demo adds a Playwright capture harness with CDP attach to your
logged-in browser, session-preservation recipes (single-device kick-out
workarounds), machine-readable endpoint specs, a replay-scaffold generator,
batch-hardening patterns (pagination, token refresh, rate pacing, baseline
verification), and a worked end-to-end example.

## License

Apache License 2.0 — see `LICENSE.txt`. Not affiliated with Anthropic;
Claude is a trademark of Anthropic, referenced only to describe
compatibility.

---

Full version — Learn-by-Demo with the capture harness, session preservation,
and replay scaffolding — is part of the Guildshelf library at
https://guildshelf.com
