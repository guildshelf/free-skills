#!/usr/bin/env python3
"""Config Doctor Lite -- read-only health scanner for AI coding agent config.

Auto-discovers CLAUDE.md files and skill directories, then runs 3 checks:

    C1  CLAUDE.md path references      (BROKEN)   backtick paths must exist
    C4  Skill directory integrity      (ORPHANED) every skill dir needs SKILL.md
    C8  SKILL.md frontmatter health    (WEAK)     name/description present

100% READ-ONLY: this script never creates, modifies, or deletes anything.

Requirements: Python 3.8+ standard library only (no third-party packages).

Usage:
    python config_doctor_lite.py [--root PATH]...

Exit codes:
    0   clean -- no findings
    1   findings reported
    2   execution error (bad arguments, nonexistent --root, internal error)

Copyright 2026 Guildshelf. Licensed under the Apache License, Version 2.0.
This is the free Lite edition; the full Config Doctor adds memory-index,
hooks, and MCP-definition checks (8 checks total) plus JSON/CI output.
"""

import argparse
import json  # noqa: F401  (kept for parity with full edition imports)
import os
import re
import sys
import time
from pathlib import Path

VERSION = "0.1.0"
SEVERITY_ORDER = {"BROKEN": 0, "ORPHANED": 1, "WEAK": 2}

BACKTICK_RE = re.compile(r"`([^`\n]+)`")
URL_SCHEME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.\-]*://")
WIN_DRIVE_RE = re.compile(r"^[A-Za-z]:[\\/]")
SKIP_DIR_NAMES = {"__pycache__", "node_modules", ".git"}


# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------

def read_text(path):
    """Read a file defensively; never raises on encoding issues."""
    return Path(path).read_text(encoding="utf-8", errors="replace")


def is_path_like(s):
    """Heuristic: does this backtick string look like a local file path?

    Whitelist approach: only strings that contain a path separator, are not
    URLs, contain no whitespace (those are usually commands), no wildcards,
    and are not purely numeric/date-like.
    """
    s = s.strip().strip("'\"")
    if not s or len(s) > 500:
        return False
    if URL_SCHEME_RE.match(s):
        return False
    if "/" not in s and "\\" not in s:
        return False
    if re.search(r"\s", s):
        return False
    if any(ch in s for ch in "*?<>|\""):
        return False
    if re.fullmatch(r"[\d.\-/\\:]+", s):        # e.g. `3/4`, `2026/07/18`
        return False
    if s.startswith("-"):                        # CLI flag like --root/path
        return False
    if re.search(r"[%$]", s):                    # unresolved env var
        return False
    return True


def candidate_paths(raw, base_dirs):
    """Yield concrete Path candidates for a raw reference string."""
    raw = raw.strip().strip("'\"").rstrip(".,;:")
    expanded = os.path.expandvars(raw)
    if re.search(r"[%$]", expanded):
        return []  # env var we cannot resolve -> skip, do not guess
    if expanded.startswith("~"):
        return [Path(os.path.expanduser(expanded))]
    if WIN_DRIVE_RE.match(expanded) or Path(expanded).is_absolute():
        return [Path(expanded)]
    cands = []
    for base in base_dirs:
        if base is not None:
            cands.append(Path(base) / expanded)
    return cands


def exists_any(cands):
    for c in cands:
        try:
            if c.exists():
                return True
        except OSError:
            continue
    return False


def parse_frontmatter(text):
    """Minimal YAML frontmatter parser (name/description use only).

    Returns dict, or None when no valid '---' fenced frontmatter exists.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    fm, key, buf, closed = {}, None, [], False
    for line in lines[1:]:
        if line.strip() == "---":
            closed = True
            break
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_\-]*):\s*(.*)$", line)
        if m and not line[:1] in (" ", "\t"):
            if key is not None:
                fm[key] = " ".join(buf).strip()
            key = m.group(1)
            val = m.group(2).strip()
            buf = [] if val in (">", "|", ">-", "|-", ">+", "|+") else [val]
        elif key is not None:
            buf.append(line.strip())
    if key is not None:
        fm[key] = " ".join(buf).strip()
    return fm if closed else None


class SystemExit2(Exception):
    """Execution error -> exit code 2."""


# --------------------------------------------------------------------------
# Scanner
# --------------------------------------------------------------------------

class Scanner:
    def __init__(self, roots):
        self.findings = []
        self.ok_refs = 0
        self.notes = []
        self._seen = set()
        self.sources = {"config_dirs": [], "claude_md_files": [], "skills_dirs": []}
        self.roots = self._validate_roots(roots)
        self._discover()

    @staticmethod
    def _validate_roots(raw_roots):
        roots = []
        for r in raw_roots:
            p = Path(os.path.expanduser(os.path.expandvars(r)))
            if not p.is_dir():
                raise SystemExit2("--root path does not exist or is not a "
                                  "directory: %s" % r)
            roots.append(p)
        return roots

    def _discover(self):
        """Discovery order: CLAUDE_CONFIG_DIR -> ~/.claude -> cwd -> --root."""
        env_dir = os.environ.get("CLAUDE_CONFIG_DIR")
        env_used = False
        if env_dir:
            p = Path(os.path.expanduser(os.path.expandvars(env_dir)))
            if p.is_dir():
                self._add_config_dir(p)
                env_used = True
            else:
                self.notes.append("CLAUDE_CONFIG_DIR is set but does not "
                                  "exist: %s (ignored)" % env_dir)
        if not env_used:
            home_claude = Path.home() / ".claude"
            if home_claude.is_dir():
                self._add_config_dir(home_claude)
            home_md = Path.home() / "CLAUDE.md"
            if home_md.is_file():
                self._add_file("claude_md_files", home_md)

        for root in [Path.cwd()] + self.roots:
            proj_md = root / "CLAUDE.md"
            if proj_md.is_file():
                self._add_file("claude_md_files", proj_md)
            proj_cfg = root / ".claude"
            if proj_cfg.is_dir():
                self._add_config_dir(proj_cfg)

    def _add_config_dir(self, cfg):
        cfg = cfg.resolve()
        if cfg in self.sources["config_dirs"]:
            return
        self.sources["config_dirs"].append(cfg)
        md = cfg / "CLAUDE.md"
        if md.is_file():
            self._add_file("claude_md_files", md)
        skills = cfg / "skills"
        if skills.is_dir():
            self._add_file("skills_dirs", skills)

    def _add_file(self, bucket, path):
        path = Path(path).resolve()
        if path not in self.sources[bucket]:
            self.sources[bucket].append(path)

    def add(self, check_id, severity, source_file, line, target, suggestion):
        key = (check_id, str(source_file), line, target)
        if key in self._seen:
            return
        self._seen.add(key)
        self.findings.append({
            "check_id": check_id,
            "severity": severity,
            "source_file": str(source_file),
            "line": line,
            "target": target,
            "suggestion": suggestion,
        })

    # -- checks -----------------------------------------------------------

    def run(self):
        for md in self.sources["claude_md_files"]:
            self.check_claude_md(md)
        for skills in self.sources["skills_dirs"]:
            self.check_skills_dir(skills)
        self.findings.sort(key=lambda f: (SEVERITY_ORDER[f["severity"]],
                                          f["check_id"], f["source_file"],
                                          f["line"] or 0))
        return self.findings

    def _resolution_bases(self, source_file):
        bases = [Path(source_file).parent]
        bases.extend(self.sources["config_dirs"])
        bases.append(Path.cwd())
        bases.extend(self.roots)
        return bases

    def check_claude_md(self, md_file):
        """C1: every backtick path-like reference must exist."""
        bases = self._resolution_bases(md_file)
        try:
            lines = read_text(md_file).splitlines()
        except OSError as e:
            self.notes.append("could not read %s: %s" % (md_file, e))
            return
        for lineno, line in enumerate(lines, 1):
            for raw in BACKTICK_RE.findall(line):
                if not is_path_like(raw):
                    continue
                ref = raw.strip().strip("'\"")
                cands = candidate_paths(ref, bases)
                if not cands:
                    continue
                if exists_any(cands):
                    self.ok_refs += 1
                else:
                    self.add("C1", "BROKEN", md_file, lineno, ref,
                             "Referenced path does not exist. Update the "
                             "reference or remove the line if the target "
                             "is gone for good.")

    def check_skills_dir(self, skills_dir):
        """C4: every skill subdirectory needs SKILL.md. C8: frontmatter."""
        try:
            subdirs = sorted(p for p in skills_dir.iterdir() if p.is_dir())
        except OSError:
            return
        for sub in subdirs:
            if sub.name.startswith(".") or sub.name in SKIP_DIR_NAMES:
                continue
            skill_md = sub / "SKILL.md"
            if not skill_md.is_file():
                self.add("C4", "ORPHANED", sub, None, sub.name,
                         "Skill directory has no SKILL.md, so the agent "
                         "cannot discover or load it. Create a SKILL.md, "
                         "move the contents elsewhere, or remove the "
                         "directory (confirm with the user first).")
                continue
            self.ok_refs += 1
            self._check_frontmatter(skill_md)

    def _check_frontmatter(self, skill_md):
        try:
            fm = parse_frontmatter(read_text(skill_md))
        except OSError:
            return
        problems = []
        if fm is None:
            problems.append("no valid '---' YAML frontmatter block")
        else:
            if not fm.get("name"):
                problems.append("missing 'name' field")
            if not fm.get("description"):
                problems.append("missing or empty 'description' field")
        if problems:
            self.add("C8", "WEAK", skill_md, 1, "; ".join(problems),
                     "Weak frontmatter hurts trigger accuracy: the agent "
                     "decides when to load a skill from its name and "
                     "description. Add a description that states what the "
                     "skill does, when to use it, and when not to.")


# --------------------------------------------------------------------------
# Reporting
# --------------------------------------------------------------------------

def summarize(findings):
    counts = {"BROKEN": 0, "ORPHANED": 0, "WEAK": 0}
    for f in findings:
        counts[f["severity"]] += 1
    return counts


def print_human(scanner, findings):
    counts = summarize(findings)
    src = scanner.sources
    print("Config Doctor Lite v%s -- scan report (checks C1, C4, C8)" % VERSION)
    print("Generated: %s" % time.strftime("%Y-%m-%d %H:%M:%S"))
    print()
    print("Scanned: %d CLAUDE.md file(s), %d skills dir(s)"
          % (len(src["claude_md_files"]), len(src["skills_dirs"])))
    print("References verified OK: %d" % scanner.ok_refs)
    for note in scanner.notes:
        print("Note: %s" % note)
    print()
    if not findings:
        print("Result: CLEAN -- no findings.")
        return
    groups = (("BROKEN", "BROKEN (must fix)"),
              ("ORPHANED", "ORPHANED (should review)"),
              ("WEAK", "WEAK (informational)"))
    idx = 0
    for sev, title in groups:
        items = [f for f in findings if f["severity"] == sev]
        if not items:
            continue
        print("%s -- %d" % (title, len(items)))
        for f in items:
            idx += 1
            line = ":%s" % f["line"] if f["line"] else ""
            print("  %2d. [%s] %s%s" % (idx, f["check_id"], f["source_file"], line))
            print("      target: %s" % f["target"])
            print("      fix:    %s" % f["suggestion"])
        print()
    print("Result: %d finding(s) -- %d broken, %d orphaned, %d weak."
          % (len(findings), counts["BROKEN"], counts["ORPHANED"], counts["WEAK"]))


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------

def build_parser():
    p = argparse.ArgumentParser(
        prog="config_doctor_lite.py",
        description="Read-only health scanner for AI coding agent config "
                    "(Lite: 3 checks). Finds broken path references in "
                    "CLAUDE.md, skill folders missing SKILL.md, and weak "
                    "SKILL.md frontmatter.",
        epilog="Exit codes: 0 = clean, 1 = findings reported, "
               "2 = execution error. The scanner never writes anything. "
               "This is the free Lite edition of the Guildshelf Config "
               "Doctor (8 checks, JSON/CI output).")
    p.add_argument("--root", action="append", default=[], metavar="PATH",
                   help="additional scan root (repeatable); use for config "
                        "kept in non-standard locations")
    p.add_argument("--version", action="version",
                   version="config-doctor-lite %s" % VERSION)
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        scanner = Scanner(args.root)
        findings = scanner.run()
    except SystemExit2 as e:
        print("config-doctor-lite: error: %s" % e, file=sys.stderr)
        return 2
    except Exception as e:  # defensive: any internal error -> exit 2
        print("config-doctor-lite: internal error: %s: %s"
              % (e.__class__.__name__, e), file=sys.stderr)
        return 2
    print_human(scanner, findings)
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
