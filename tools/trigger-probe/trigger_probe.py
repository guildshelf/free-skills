#!/usr/bin/env python3
"""trigger-probe — measure whether a Claude Code skill actually fires.

A skill's description is a bet: that when a user phrases a request their own way,
the model will decide to load your package. Nothing about writing a good
description tells you whether you won that bet. This runs the experiment.

For each case it starts a **fresh** headless session (`claude -p`), passes the
prompt through verbatim, and records which skill — if any — the model chose to
load. Then it scores the positive cases (should fire) against the negative ones
(should stay quiet) and writes a scorecard you can publish.

Apache-2.0. Standard library only. No network calls of its own; the `claude` CLI
does its own thing.

    # from a cases file
    python trigger_probe.py cases.md --slug my-skill --skills-dir .claude/skills

    # from an installed plugin, which is how customers actually have it
    python trigger_probe.py cases.md --slug my-skill \
        --plugin-dir path/to/plugins/my-plugin

    # write the artefacts
    python trigger_probe.py cases.md --slug my-skill --skills-dir .claude/skills \
        --results results.json --card scorecard.md

Cases file format — either a numbered list or a markdown table, under two
headings. Both of these parse:

    ## Should trigger
    1. "Scan this repo for hardcoded secrets before I publish."
    2. "Check if I leaked an API key in here."

    ## Should NOT trigger
    | ID | Prompt | Why it should lose |
    |----|--------|--------------------|
    | N1 | Rotate my AWS keys | remediation, not scanning |

Exit codes: 0 both sides at or above the bar | 1 below the bar or cases unrun |
2 could not run.

## Three things we learned the hard way

**Your working directory changes the answer.** Run the same cases in an empty
directory and in a realistic project and you will get different numbers. "Audit my
dotfiles for anything sensitive" cannot fire properly when there are no dotfiles —
the model looks around instead of loading anything. Measure in a directory that
looks like your users' directory, and say which one you used when you publish a
number.

**One 20-case run cannot resolve a 90% bar.** Boundary cases are genuinely
stochastic. We repeated two of ours five times each: one fired 40% of the time, the
other 80%. If your verdict is a pass by one case, it is a pass by one case. Use
`--repeat` on the cases you do not trust.

**Install the whole library, not the skill alone.** With siblings absent, the
negative side means nothing — there is nothing for a near-miss prompt to lose to.
And when a sibling *does* win, that is often correct: your skill's trigger rate and
your library's correctness are different numbers.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

VERSION = "0.1.0"

POS_HEAD = re.compile(r"^#{1,6}\s*should\s+trigger", re.I)
NEG_HEAD = re.compile(r"^#{1,6}\s*should\s+not\s+trigger", re.I)
ANY_HEAD = re.compile(r"^#{1,6}\s")
NUMBERED = re.compile(r"^\s*\d+[.)]\s*(.+?)\s*$")
TABLE_SEP = re.compile(r"^[\s:|-]+$")
# A short label, not a sentence: P1, N01, T10, TC-04.
ID_CELL = re.compile(r"^[A-Za-z]{0,3}[-_ ]?\d{1,3}$")
HEADER_CELL = re.compile(r"^(id|#|no\.?|prompt|case|expected|note|reason|why)$", re.I)


# ------------------------------------------------------------------- parsing
def parse_table_row(line: str):
    """(prompt, note) from a markdown row, or None if it is not a case.

    Position, not length. A table's columns are fixed by its header, so the prompt
    is the first cell after the ID. Picking the longest cell instead — which is the
    obvious shortcut — breaks the moment a "why" column runs longer than a short
    prompt, and it breaks silently: you score the explanation instead of the prompt.
    """
    if TABLE_SEP.match(line.strip()):
        return None
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    cells = [c for c in cells if c]
    if not cells:
        return None
    if HEADER_CELL.match(cells[0]) or all(HEADER_CELL.match(c) for c in cells):
        return None
    body = cells[1:] if ID_CELL.match(cells[0]) else cells
    if not body:
        return None
    return body[0], (body[1] if len(body) > 1 else "")


def parse_cases(path: Path) -> list[dict]:
    """Read a cases file into [{id, expected, prompt, note}]."""
    side = None
    pos, neg = [], []
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.rstrip()
        if ANY_HEAD.match(line):
            # NEG first: "Should NOT trigger" must not be read as "Should trigger".
            side = "neg" if NEG_HEAD.match(line) else ("pos" if POS_HEAD.match(line) else None)
            continue
        if side is None or not line.strip():
            continue
        if line.lstrip().startswith("|"):
            row = parse_table_row(line)
            if not row:
                continue
            prompt, note = row
        else:
            m = NUMBERED.match(line)
            if not m:
                continue
            prompt, note = m.group(1), ""
            tail = re.match(r"^(.*?)\s*\(([^()]*)\)\s*$", prompt)
            if tail:
                prompt, note = tail.group(1), tail.group(2)
        prompt = prompt.strip().strip('"').strip("*").strip().strip('"').strip()
        if prompt:
            (pos if side == "pos" else neg).append({"prompt": prompt, "note": note})

    cases = []
    for i, c in enumerate(pos, 1):
        cases.append({"id": f"P{i:02d}", "expected": "trigger", **c})
    for i, c in enumerate(neg, 1):
        cases.append({"id": f"N{i:02d}", "expected": "silent", **c})
    return cases


def load_manifest(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data["cases"] if isinstance(data, dict) and "cases" in data else data


# ------------------------------------------------------------------- running
def build_cmd(prompt: str, a) -> list[str]:
    cmd = [
        a.claude, "-p", prompt,
        "--output-format", "stream-json", "--verbose",
        "--no-session-persistence",
        "--tools", a.tools,
        "--model", a.model,
    ]
    if a.plugin_dir:
        cmd += ["--plugin-dir", a.plugin_dir]
    # Keep the operator's own user-level skills out of the run; a personal skill
    # collection will happily win cases your customers would give to you.
    cmd += ["--setting-sources", a.setting_sources]
    if a.no_mcp:
        cmd += ["--mcp-config", '{"mcpServers":{}}', "--strict-mcp-config"]
    if a.budget:
        cmd += ["--max-budget-usd", str(a.budget)]
    return cmd


def run_case(prompt: str, a) -> dict:
    """Return {loaded, why, seconds}. Killed as soon as the verdict is known."""
    started = time.monotonic()
    try:
        p = subprocess.Popen(
            build_cmd(prompt, a), cwd=a.lab, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL, text=True,
            encoding="utf-8", errors="replace", bufsize=1,
        )
    except FileNotFoundError:
        return {"loaded": None, "why": f"{a.claude} not on PATH", "seconds": 0.0, "fatal": True}

    loaded, why, first_other = None, "", ""
    try:
        assert p.stdout is not None
        for line in p.stdout:
            if time.monotonic() - started > a.timeout:
                why = "timeout"
                break
            line = line.strip()
            if not line.startswith("{"):
                continue
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            if ev.get("type") == "assistant":
                done = False
                for b in ev.get("message", {}).get("content", []) or []:
                    if b.get("type") != "tool_use":
                        continue
                    if b.get("name") == "Skill":
                        loaded = str(b.get("input", {}).get("skill", "?"))
                        why, done = "skill-tool", True
                    elif a.first_action_only:
                        loaded, why, done = None, f"first tool was {b.get('name')}", True
                    else:
                        # Keep watching: a skill loaded after a manual step still
                        # loaded. Whether that counts is a real choice, so it is a
                        # flag rather than an assumption.
                        first_other = first_other or str(b.get("name"))
                    if done:
                        break
                if why:
                    break
            elif ev.get("type") == "result":
                why = why or (f"whole turn, never loaded (worked via {first_other})"
                              if first_other else "turn ended with no tool call")
                break
    finally:
        p.kill()
        try:
            p.wait(timeout=15)
        except subprocess.TimeoutExpired:
            pass
    return {"loaded": loaded, "why": why, "seconds": round(time.monotonic() - started, 1)}


# ------------------------------------------------------------------- scoring
def score(cases: list[dict], results: dict, bar: float) -> dict:
    pos = [c for c in cases if c["expected"] == "trigger"]
    neg = [c for c in cases if c["expected"] != "trigger"]
    unrun = [c["id"] for c in cases if results.get(c["id"], {}).get("triggered") is None]
    fired_pos = sum(1 for c in pos if results.get(c["id"], {}).get("triggered"))
    fired_neg = sum(1 for c in neg if results.get(c["id"], {}).get("triggered"))
    trig = fired_pos / len(pos) if pos else 0.0
    restr = (len(neg) - fired_neg) / len(neg) if neg else 0.0
    return {
        "trigger": f"{fired_pos}/{len(pos)}", "trigger_rate": round(trig, 3),
        "restraint": f"{len(neg) - fired_neg}/{len(neg)}", "restraint_rate": round(restr, 3),
        "bar": bar, "unrun": unrun,
        "verdict": "INCOMPLETE" if unrun else ("PASS" if trig >= bar and restr >= bar else "FAIL"),
        "misses": [{"id": c["id"], "prompt": c["prompt"],
                    "why": results.get(c["id"], {}).get("note", "")}
                   for c in pos if not results.get(c["id"], {}).get("triggered")],
        "false_fires": [{"id": c["id"], "prompt": c["prompt"]}
                        for c in neg if results.get(c["id"], {}).get("triggered")],
    }


def render_card(slug: str, rep: dict, a) -> str:
    out = [
        f"# Trigger scorecard — {slug}", "",
        f"- Measured with trigger-probe {VERSION}, model `{a.model}`",
        f"- Fresh session per case; " + (
            "whole plugin installed" if a.plugin_dir else f"skills from `{a.setting_sources}` settings"),
        f"- Counted as fired: the `Skill` tool was called for `{slug}`"
        + (" as the model's first action" if a.first_action_only else " at any point in the turn"),
        f"- Pass bar: {int(rep['bar'] * 100)}% on each side", "",
        "| Measure | Result |", "|---|---|",
        f"| Fires when it should | **{rep['trigger']}** ({int(rep['trigger_rate']*100)}%) |",
        f"| Stays quiet when it should | **{rep['restraint']}** ({int(rep['restraint_rate']*100)}%) |",
        "", f"**Verdict: {rep['verdict']}**", "",
    ]
    if rep["unrun"]:
        out += [f"Unrun cases: {', '.join(rep['unrun'])} — an incomplete eval that reads "
                f"as a pass is worse than no eval.", ""]
    if rep["misses"]:
        out += ["## Should have fired, did not", ""]
        out += [f"- `{m['id']}` \"{m['prompt']}\"" + (f" — {m['why']}" if m["why"] else "")
                for m in rep["misses"]] + [""]
    if rep["false_fires"]:
        out += ["## Fired when it should not", ""]
        out += [f"- `{f['id']}` \"{f['prompt']}\"" for f in rep["false_fires"]] + [""]
    out += [
        "## What this does and does not measure", "",
        "Trigger accuracy only — whether the skill loads for the prompts it claims and",
        "stays out of the way otherwise. It says nothing about whether the skill's",
        "instructions are correct once loaded.", "",
        "Read the number with its caveats: the working directory changes results, and a",
        "single 20-case run cannot resolve a 90% bar, because boundary cases are",
        "stochastic. If this verdict is a pass by one case, treat it as a pass by one case.",
        "",
    ]
    return "\n".join(out)


# ----------------------------------------------------------------------- CLI
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="trigger_probe", description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cases", help="a cases.md, or a manifest JSON with a 'cases' array")
    ap.add_argument("--slug", required=True, help="the skill name as the agent sees it")
    ap.add_argument("--plugin-dir", help="install a whole plugin for the run (recommended)")
    ap.add_argument("--skills-dir", help="informational: where your skills live, for the card")
    ap.add_argument("--setting-sources", default="project",
                    help="claude --setting-sources value (default: project, which keeps "
                         "your personal user-level skills out of the run)")
    ap.add_argument("--lab", default=".", help="working directory for each session")
    ap.add_argument("--model", default="sonnet")
    ap.add_argument("--tools", default="Skill,Read,Glob,Grep",
                    help="tools available to the session")
    ap.add_argument("--claude", default="claude", help="path to the claude CLI")
    ap.add_argument("--budget", type=float, default=0.15, help="max USD per case, 0 to disable")
    ap.add_argument("--timeout", type=float, default=150, help="seconds per case")
    ap.add_argument("--bar", type=float, default=0.9, help="pass bar per side")
    ap.add_argument("--repeat", type=int, default=1,
                    help="run each case N times; fires if it fired in any run, and the "
                         "per-case counts are reported so you can see the variance")
    ap.add_argument("--first-action-only", action="store_true",
                    help="count only skills loaded as the model's first action (stricter)")
    ap.add_argument("--no-mcp", action="store_true", default=True,
                    help="disable MCP servers for the run (default)")
    ap.add_argument("--only", help="comma-separated case IDs")
    ap.add_argument("--results", help="write the raw results JSON here")
    ap.add_argument("--card", help="write a publishable scorecard here")
    ap.add_argument("--version", action="version", version=f"trigger-probe {VERSION}")
    a = ap.parse_args(argv)

    src = Path(a.cases)
    if not src.is_file():
        print(f"error: no such file: {src}", file=sys.stderr)
        return 2
    try:
        cases = load_manifest(src) if src.suffix == ".json" else parse_cases(src)
    except (json.JSONDecodeError, KeyError, OSError) as exc:
        print(f"error: cannot read cases: {exc}", file=sys.stderr)
        return 2
    if a.only:
        want = {x.strip() for x in a.only.split(",")}
        cases = [c for c in cases if c["id"] in want]
    if not cases:
        print("error: parsed 0 cases — check the '## Should trigger' / "
              "'## Should NOT trigger' headings", file=sys.stderr)
        return 2

    print(f"{len(cases)} cases · model {a.model} · target {a.slug}"
          + (f" · {a.repeat} repeats" if a.repeat > 1 else ""))
    print(f"working directory: {Path(a.lab).resolve()}\n")

    results: dict[str, dict] = {}
    for i, c in enumerate(cases, 1):
        fires, notes = 0, []
        for _ in range(max(1, a.repeat)):
            r = run_case(c["prompt"], a)
            if r.get("fatal"):
                print(f"error: {r['why']}", file=sys.stderr)
                return 2
            got = (r["loaded"] or "").split(":")[-1]
            if got == a.slug:
                fires += 1
            elif r["loaded"]:
                notes.append(f"{r['loaded']} loaded instead")
            else:
                notes.append(r["why"])
        fired = fires > 0
        note = "" if fired and a.repeat == 1 else "; ".join(dict.fromkeys(notes))[:200]
        if a.repeat > 1:
            note = (f"fired {fires}/{a.repeat}" + (f" — {note}" if note else ""))
        results[c["id"]] = {"triggered": fired, "note": note}
        want_fire = c["expected"] == "trigger"
        ok = "ok  " if fired == want_fire else "MISS"
        print(f"[{i:2}/{len(cases)}] {c['id']} {'FIRED' if fired else 'quiet'} {ok}"
              f" ({'want fire' if want_fire else 'want quiet'})"
              + (f" {note}" if note else ""))

    rep = score(cases, results, a.bar)
    print(f"\n{a.slug}: trigger {rep['trigger']} ({int(rep['trigger_rate']*100)}%), "
          f"restraint {rep['restraint']} ({int(rep['restraint_rate']*100)}%) "
          f"-> {rep['verdict']} (bar {int(a.bar*100)}%)")
    for m in rep["misses"]:
        print(f"  MISS {m['id']}: {m['prompt'][:70]!r}")
    for f in rep["false_fires"]:
        print(f"  FALSE FIRE {f['id']}: {f['prompt'][:70]!r}")

    if a.results:
        Path(a.results).write_text(
            json.dumps({"slug": a.slug, "probe_version": VERSION, "model": a.model,
                        "report": rep, "results": results}, indent=2), encoding="utf-8")
        print(f"\nwrote {a.results}")
    if a.card:
        Path(a.card).write_text(render_card(a.slug, rep, a), encoding="utf-8")
        print(f"wrote {a.card}")

    return 0 if rep["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
