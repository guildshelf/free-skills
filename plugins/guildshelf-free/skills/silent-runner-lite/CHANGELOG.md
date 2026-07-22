# Changelog

All notable changes to Silent Runner Lite are documented here.
This project adheres to [Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-07-18

### Added

- Initial open-source release of **Silent Runner Lite** (Apache-2.0), the
  free edition of the Guildshelf Silent Runner.
- `scripts/silent_run.vbs` — generic no-window command wrapper
  (window style 0, non-blocking).
- `SKILL.md` — the three core patterns: VBS wrapper for `shell:startup`,
  `Start-Process -WindowStyle Hidden` for `.bat` children, and
  `pythonw` / `CREATE_NO_WINDOW` for Python, plus a pitfalls table.
- `examples/startup.vbs.example` and `examples/background-launch.bat.example` —
  copy-paste templates with placeholder paths.
- `eval/cases.md` — 20 trigger / non-trigger evaluation cases.
- `LICENSE.txt` — Apache License 2.0.

### Notes

- Windows only. Not for macOS/Linux, not for hiding software from security
  tooling, and not a scheduler/cron manager.
- Lite scope: no-window launching only. Focus guard, `ForegroundLockTimeout`
  fix, Task Scheduler batch conversion, and pop-up diagnostics are in the
  full Silent Runner.
