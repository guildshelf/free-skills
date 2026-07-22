# Silent Runner Lite

Run any Windows background process — `.bat`, `node`, `python`, `.exe` — with
**zero visible window and zero console flash**. The Lite edition ships the
three patterns that solve 90% of "why does a black window keep popping"
problems, plus a ready-to-run VBS wrapper.

- `scripts/silent_run.vbs` — generic no-window wrapper:
  `wscript.exe silent_run.vbs <program> [args...]`
- Pattern 1 — VBS wrapper for the startup folder (`shell:startup`)
- Pattern 2 — `Start-Process -WindowStyle Hidden` for children of a `.bat`
  (never `start /min`)
- Pattern 3 — `pythonw.exe` + `CREATE_NO_WINDOW` for Python
- `examples/` — copy-paste templates for both launch styles

Windows only. Not for hiding software from antivirus or security tooling —
these patterns quiet *legitimate* processes for the machine's own user.

## Quick start

```
wscript.exe scripts\silent_run.vbs cmd /c my-script.bat
```

For login-time autostart: copy `examples/startup.vbs.example`, edit two
lines, drop the `.vbs` (never the `.bat`) into `shell:startup`.

## Use as an agent skill

Drop this folder into your agent's skills directory (for Claude Code:
`~/.claude/skills/silent-runner-lite/`). The `SKILL.md` covers when to apply
each pattern and the common pitfalls table.

## What the Lite edition deliberately leaves out

Honest scope: Lite covers no-window **launching** only. The full Silent Runner
adds a focus guard (minimizes stray automation windows and returns focus to
your editor), a reversible `ForegroundLockTimeout` fix, batch conversion of
existing Task Scheduler jobs (auto-backup, idempotent, dry-run), and
60-second diagnostics that identify which process keeps popping windows.

## License

Apache License 2.0 — see `LICENSE.txt`. Not affiliated with Anthropic;
Claude is a trademark of Anthropic, referenced only to describe
compatibility.

---

Full version — Silent Runner with focus guard, Task Scheduler batch
conversion, and pop-up diagnostics — is part of the Guildshelf library at
https://guildshelf.com
