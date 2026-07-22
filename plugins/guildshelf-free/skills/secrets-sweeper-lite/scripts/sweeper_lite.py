#!/usr/bin/env python3
"""Secrets Sweeper Lite -- offline scan for the 10 most dangerous credential
types before you publish, open-source, or hand off a directory.

Scans a directory (or single file) line by line against 10 high-confidence
detection rules and prints MASKED findings to the terminal. Nothing is
written to disk and nothing leaves your machine.

Privacy guarantees:
  * Python standard library only; no network-capable modules are imported.
  * Output never contains a full secret -- matches are masked (first 4 +
    last 2 characters kept, the rest starred).

Exit codes:
  0  clean (no findings)
  1  findings reported
  2  execution error (bad target, ...)

All illustrative values in this file are fabricated or written in a
constructed (non-matchable) form so that scanning this package with its own
engine yields zero findings.

Copyright 2026 Guildshelf. Licensed under the Apache License, Version 2.0.
This is the free Lite edition; the full Secrets Hygiene Sweeper adds ~30 more
rules (PII, IPs, tunnel domains, personal paths), custom denylists, and
exportable masked Markdown/JSON reports.
"""

from __future__ import annotations

import argparse
import math
import os
import re
import sys

TOOL_NAME = "secrets-sweeper-lite"
VERSION = "0.1.0"

DEFAULT_EXCLUDED_DIRS = {
    ".git", ".hg", ".svn", "node_modules", "__pycache__", "venv", ".venv",
    "dist", "build", ".tox", ".mypy_cache", ".pytest_cache",
}

MAX_FILE_BYTES = 5 * 1024 * 1024


# --------------------------------------------------------------------------
# The 10 rules (id, severity, pattern, value_group, entropy_min)
# --------------------------------------------------------------------------

RULES = [
    ("private-key-block", "critical",
     r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP |ENCRYPTED )?PRIVATE KEY(?: BLOCK)?-----",
     0, 0.0),
    ("aws-access-key-id", "critical",
     r"\b(?:A3T[A-Z0-9]|AKIA|ASIA|ABIA|ACCA)[A-Z0-9]{16}\b",
     0, 0.0),
    ("github-token", "critical",
     r"\b(?:(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36,255}|github_pat_[A-Za-z0-9_]{22,255})\b",
     0, 0.0),
    ("openai-key", "critical",
     r"\b(?:sk-[A-Za-z0-9]{20}T3BlbkFJ[A-Za-z0-9]{20}|sk-proj-[A-Za-z0-9_-]{40,})\b",
     0, 0.0),
    ("anthropic-key", "critical",
     r"\bsk-ant-[A-Za-z0-9_-]{24,}\b",
     0, 0.0),
    ("google-api-key", "critical",
     r"\bAIza[0-9A-Za-z_-]{35}\b",
     0, 0.0),
    ("slack-token", "critical",
     r"\bxox[baprs]-[0-9A-Za-z-]{10,}\b",
     0, 0.0),
    ("stripe-live-secret-key", "critical",
     r"\b[sr]k_live_[0-9a-zA-Z]{24,}\b",
     0, 0.0),
    ("jwt", "high",
     r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{5,}\b",
     0, 0.0),
    ("generic-credential-assignment", "high",
     r"(?i)\b(api[_-]?key|apikey|secret|token|passwd|password|credential|"
     r"access[_-]?key|auth[_-]?token)\b\s*[:=]\s*['\"]([^\s'\"]{8,})['\"]",
     2, 3.0),
]

COMPILED = [(rid, sev, re.compile(pat), grp, ent)
            for rid, sev, pat, grp, ent in RULES]


# --------------------------------------------------------------------------
# False-positive suppression (placeholders never get reported)
# --------------------------------------------------------------------------

_PLACEHOLDER_RE = re.compile(
    r"(?i)(your[_-]|x{4,}|\*{3,}|change[_-]?me|example|sample|dummy|"
    r"placeholder|redacted|todo|fixme|123456|abcdef)"
)
_ANGLE_BRACKET_RE = re.compile(r"^<[^>]+>$")


def is_placeholder_value(value: str) -> bool:
    v = value.strip()
    if not v:
        return True
    if _ANGLE_BRACKET_RE.match(v):
        return True
    if _PLACEHOLDER_RE.search(v):
        return True
    return False


def shannon_entropy(s: str) -> float:
    """Shannon entropy in bits per character."""
    if not s:
        return 0.0
    freq: dict = {}
    for ch in s:
        freq[ch] = freq.get(ch, 0) + 1
    n = len(s)
    return -sum((c / n) * math.log2(c / n) for c in freq.values())


def mask_value(value: str) -> str:
    """First 4 + last 2 characters kept; everything else starred.
    Short values are fully or near-fully starred so nothing is recoverable."""
    n = len(value)
    if n <= 6:
        return "*" * n
    if n <= 10:
        return value[:2] + "*" * (n - 3) + value[-1:]
    return value[:4] + "*" * (n - 6) + value[-2:]


def is_binary_file(path: str) -> bool:
    try:
        with open(path, "rb") as fh:
            chunk = fh.read(8192)
    except OSError:
        return True
    return b"\x00" in chunk


# --------------------------------------------------------------------------
# Scanning
# --------------------------------------------------------------------------

def scan_line(line: str):
    findings = []
    for rule_id, severity, rx, value_group, entropy_min in COMPILED:
        for m in rx.finditer(line):
            value = m.group(value_group)
            if is_placeholder_value(value):
                continue
            if entropy_min > 0 and shannon_entropy(value) < entropy_min:
                continue
            findings.append({
                "rule_id": rule_id,
                "severity": severity,
                "col": m.start(value_group) + 1,
                "match_masked": mask_value(value),
            })
    return findings


def iter_files(root: str):
    if os.path.isfile(root):
        yield root, os.path.basename(root)
        return
    base = root
    for dirpath, dirnames, filenames in os.walk(root, topdown=True):
        dirnames[:] = [d for d in dirnames if d not in DEFAULT_EXCLUDED_DIRS]
        for fn in filenames:
            fpath = os.path.join(dirpath, fn)
            yield fpath, os.path.relpath(fpath, base).replace(os.sep, "/")


def scan_target(root: str):
    findings = []
    files_scanned = 0
    files_skipped = 0
    for fpath, rel in iter_files(root):
        try:
            if os.path.getsize(fpath) > MAX_FILE_BYTES:
                files_skipped += 1
                continue
        except OSError:
            files_skipped += 1
            continue
        if is_binary_file(fpath):
            files_skipped += 1
            continue
        files_scanned += 1
        try:
            with open(fpath, encoding="utf-8", errors="replace") as fh:
                for lineno, raw in enumerate(fh, 1):
                    line = raw.rstrip("\r\n")
                    if not line.strip():
                        continue
                    for f in scan_line(line):
                        f["file"] = rel
                        f["line"] = lineno
                        findings.append(f)
        except OSError:
            files_skipped += 1
    return findings, files_scanned, files_skipped


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def build_parser():
    p = argparse.ArgumentParser(
        prog="sweeper_lite.py",
        description=("Offline scan for the 10 most dangerous credential types "
                     "(private keys, AWS/GitHub/OpenAI/Anthropic/Google/Slack/"
                     "Stripe keys, JWTs, generic credential assignments). "
                     "Prints masked findings to the terminal; stdlib only, "
                     "zero network calls, writes nothing to disk."),
        epilog=("exit codes: 0 clean | 1 findings | 2 execution error. "
                "This is the free Lite edition of the Guildshelf Secrets "
                "Hygiene Sweeper."))
    p.add_argument("target", nargs="?",
                   help="directory or file to scan (required unless --list-rules)")
    p.add_argument("--list-rules", action="store_true",
                   help="print the 10-rule table and exit")
    p.add_argument("--quiet", action="store_true",
                   help="suppress banner; print findings and summary only")
    p.add_argument("--version", action="version",
                   version=f"{TOOL_NAME} {VERSION}")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)

    if args.list_rules:
        print(f"{'rule_id':34} severity")
        for rid, sev, _rx, _grp, _ent in COMPILED:
            print(f"{rid:34} {sev}")
        return 0

    if not args.target:
        print("error: target is required (or use --list-rules)", file=sys.stderr)
        return 2
    if not os.path.exists(args.target):
        print(f"error: target not found: {args.target}", file=sys.stderr)
        return 2

    if not args.quiet:
        print(f"{TOOL_NAME} v{VERSION} -- offline scan (no network calls, "
              "no files written)")

    try:
        findings, files_scanned, files_skipped = scan_target(args.target)
    except OSError as e:
        print(f"error: scan failed: {e}", file=sys.stderr)
        return 2

    findings.sort(key=lambda f: (f["severity"] != "critical", f["file"],
                                 f["line"], f["col"]))

    for f in findings:
        print(f"{f['severity'].upper():8} {f['file']}:{f['line']}:{f['col']} "
              f"{f['rule_id']}  {f['match_masked']}")

    crit = sum(1 for f in findings if f["severity"] == "critical")
    high = len(findings) - crit
    print(f"scanned {files_scanned} files (skipped {files_skipped}) | "
          f"findings: {len(findings)} (critical: {crit}, high: {high})")
    if findings:
        print("FAIL: rotate every CRITICAL credential at its provider first, "
              "replace with environment variables, then re-scan to zero.")
    else:
        print("PASS: no findings.")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
