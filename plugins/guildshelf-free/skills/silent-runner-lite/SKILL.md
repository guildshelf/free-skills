---
name: silent-runner-lite
description: >-
  Launch a Windows background process (.bat, node, python, .exe) with no
  visible console window — no black console flash on login or restart. Provides a
  generic VBS launch wrapper (window style 0) for the startup folder, the
  Start-Process -WindowStyle Hidden pattern for child processes inside a
  .bat, and the pythonw / CREATE_NO_WINDOW patterns for Python. Use when a
  script, bot, or dev server keeps popping a command window or flashing a
  console on startup/login and you want it fully silent. Windows only.
  NOT for macOS or Linux, NOT for hiding malware or evading security
  software, NOT a scheduler/cron manager, and this Lite edition does not
  include focus-steal governance, pop-up diagnostics, or batch-hiding of
  existing Task Scheduler jobs (the full Silent Runner covers those).
---

# Silent Runner Lite

Run a Windows background process with **zero pop-up windows**. This Lite
edition bundles the three core patterns plus a ready-to-run VBS wrapper so
that scripts, bots, and dev servers never flash a black console at you.

## 1. When to use / When NOT to use

**Use this skill when:**

- A `.bat`, `node`, `python`, or `.exe` process keeps popping a command
  window every time it starts or restarts.
- A script you dropped into the Windows startup folder (`shell:startup`)
  flashes a console on every login.
- You are wiring up a background service and want it silent from day one.

**Do NOT use this skill for:**

- **macOS or Linux.** This skill is Windows-only. For `launchd`, `systemd`,
  `nohup`, or cron, use a platform-appropriate approach instead.
- **Hiding malware or evading antivirus / Task Manager / EDR.** These
  patterns make *legitimate* background processes quiet for the user who owns
  the machine. They are not obfuscation and must not be used to conceal
  software from security tooling. If that is the request, decline it.
- **Creating or managing scheduled jobs.** This skill silences the *window*;
  it does not create, delete, or schedule jobs.

## 2. Quick decision table

| Situation | Correct approach | Do NOT use |
|---|---|---|
| `.bat` placed in the Windows startup folder | VBS wrapper (`silent_run.vbs`) | dropping the `.bat` in directly |
| Launching a child process from inside a `.bat` | `Start-Process -WindowStyle Hidden` | `start /min` |
| Python script | `pythonw.exe` | `python.exe` |
| Child process spawned from Python | `creationflags=0x08000000` (CREATE_NO_WINDOW) | default `Popen` |

**The rule: not a single millisecond of a visible window.** Pick the matching
row above and use exactly that method.

## 3. Pattern 1 — VBS wrapper for `shell:startup`

Any `.bat` that goes into `shell:startup` (run automatically at login) should
be wrapped in a VBS launcher instead of placed directly:

```vbs
Dim objShell
Set objShell = CreateObject("WScript.Shell")
objShell.CurrentDirectory = "C:\path\to\your\project"
objShell.Run "cmd /c your-script.bat", 0, False
```

- `0` = the window is never shown.
- `False` = do not wait for completion (the VBS exits immediately; the `.bat`
  keeps running in the background).
- **Put the `.vbs` in the startup folder, never the `.bat`.**

The generic wrapper `scripts/silent_run.vbs` does this for any command:

```
wscript.exe silent_run.vbs <program> [args...]
```

See `examples/startup.vbs.example` for a startup-folder template.

## 4. Pattern 2 — background child process (no window) inside a `.bat`

```bat
:: WRONG - this pops a minimized window on the taskbar
start "" /min node server.js

:: RIGHT - no visible window
powershell -WindowStyle Hidden -NoProfile -Command "Start-Process 'node' -ArgumentList 'server.js' -WindowStyle Hidden"
```

With a working directory (works even when the path contains non-ASCII
characters):

```bat
cd /d "C:\path\to\your\project"
powershell -WindowStyle Hidden -NoProfile -Command "Start-Process 'node' -ArgumentList 'server.js' -WindowStyle Hidden"
```

`Start-Process` inherits the current working directory of `cmd`, so you can
omit `-WorkingDirectory`. See `examples/background-launch.bat.example`.

## 5. Pattern 3 — silent Python

```bat
:: run a script with pythonw.exe (no console window)
pythonw.exe your_script.py

:: wrap pythonw.exe in VBS for the startup folder
objShell.Run """C:\path\to\pythonw.exe"" ""C:\path\to\your\script.py""", 0, False
```

Spawning a child process from inside Python without a window:

```python
import subprocess, sys

NOWIN = 0x08000000 if sys.platform == "win32" else 0   # CREATE_NO_WINDOW

proc = subprocess.Popen(
    ["node", "server.js"],
    cwd="C:/path/to/your/project",
    creationflags=NOWIN,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)
```

## 6. Common pitfalls

| Pitfall | Symptom | Fix |
|---|---|---|
| `start /min` | minimized window appears on the taskbar | `Start-Process -WindowStyle Hidden` |
| dropping a `.bat` in the startup folder | CMD window pops on login | use a VBS wrapper |
| `pause` at the end of a `.bat` | zombie `cmd.exe` process | remove `pause` |
| `python.exe` for a long-running service | a Python window appears | `pythonw.exe` |
| `start` without `/b` in a loop `.bat` | a window flashes on every restart | `Start-Process` or `start /b` |

## 7. Safety & scope

- **Windows only.** No macOS / Linux support in this skill.
- **Not for concealment.** These patterns quiet legitimate background
  processes for the machine's own user. They must not be used to hide
  software from antivirus, EDR, Task Manager, or any security control.
- **No outcome guarantees.** These are tools; they do not promise unattended
  operation.
- **Antivirus note.** Window-management techniques like these are commonly
  flagged by antivirus heuristics (a VBS spawning `cmd.exe` is a classic
  trigger). That is expected, not proof of malice. If your AV blocks a
  wrapper you have read and trust, add a per-file allowlist exclusion —
  never disable protection wholesale. The full Silent Runner documents the
  expected flags per component and includes an allowlist guide.

## 8. Lite vs. full

This Lite edition covers no-window *launching* end to end. The full
**Silent Runner** adds: a focus guard that minimizes stray automation windows
and returns focus to your work, a reversible user-level
`ForegroundLockTimeout` fix, batch conversion of existing Task Scheduler jobs
to run without a console window (auto-backup, idempotent, dry-run), and 60-second diagnostic
monitors that catch whatever keeps popping windows on your machine.

---

*No affiliation with Anthropic. Claude and Claude Code are trademarks of
Anthropic, referenced here only to describe compatibility.*
