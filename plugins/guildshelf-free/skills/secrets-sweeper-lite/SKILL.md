---
name: secrets-sweeper-lite
description: Quick offline scan of a directory for the 10 most dangerous
  hardcoded credential types before publishing or sharing — private key blocks,
  AWS access keys, GitHub tokens, OpenAI / Anthropic / Google API keys, Slack
  tokens, Stripe live keys, JWTs, and generic key/secret/token assignments
  (entropy-checked). Prints masked findings straight to the terminal with
  CI-friendly exit codes; Python stdlib only, zero network calls, writes
  nothing to disk. Use when the user says "scan for secrets", "check for
  leaked keys", "did I hardcode a key somewhere", or before open-sourcing or
  handing off a repo. NOT for rotating or revoking credentials, scanning git
  history (working tree only), PII / IP-address / tunnel-domain /
  personal-path detection, custom denylists (names, internal terms), or
  exportable Markdown/JSON reports — those are in the full Secrets Hygiene
  Sweeper.
---

# Secrets Sweeper Lite

Scan anything you are about to publish, open-source, or hand to a contractor
for the ten credential types that hurt the most — and get masked terminal
findings before it leaves your machine.

## When to use / when not to use

Use this skill when:

- You are about to publish or open-source a directory and want a fast check
  that it contains no hardcoded keys or tokens.
- You suspect a key was hardcoded somewhere in a project and want it located.
- You want a lightweight CI gate that fails a build when a credential appears
  (exit code 1 on any finding).

Do NOT use this skill for:

- Rotating, revoking, or validating credentials — the findings tell you where
  to rotate; the action is yours.
- Scanning git history — this scans the working tree only.
- PII coverage (emails, phone numbers, IPs, personal paths) or custom
  denylist terms (person names, internal codenames) — full version territory.
- Runtime secret management — this is not a vault or a .env loader.
- Malware or prompt-injection detection — out of scope by design.

## Quick start

```
python scripts/sweeper_lite.py <target-dir>
```

That one line scans `<target-dir>` recursively, prints masked findings to the
terminal, and exits `1` if anything was found (`0` clean, `2` error).

```
python scripts/sweeper_lite.py --list-rules     # print the 10-rule table
python scripts/sweeper_lite.py <dir> --quiet    # findings + summary only
```

## The 10 rules

| # | rule_id | Severity | Catches |
|---|---|---|---|
| 1 | private-key-block | CRITICAL | PEM / OpenSSH / PGP private key headers |
| 2 | aws-access-key-id | CRITICAL | AWS access key IDs |
| 3 | github-token | CRITICAL | GitHub classic + fine-grained tokens |
| 4 | openai-key | CRITICAL | OpenAI classic + project-scoped keys |
| 5 | anthropic-key | CRITICAL | Anthropic API keys |
| 6 | google-api-key | CRITICAL | Google API keys |
| 7 | slack-token | CRITICAL | Slack bot/user/app tokens |
| 8 | stripe-live-secret-key | CRITICAL | Stripe live secret/restricted keys |
| 9 | jwt | HIGH | Signed JSON Web Tokens |
| 10 | generic-credential-assignment | HIGH | `key/secret/token/password = "..."` assignments, entropy-checked |

## Reading the output

- Each finding prints as `SEVERITY file:line:col rule_id masked-match`.
- **Matches are masked** — first 4 + last 2 characters kept, the rest starred.
  The output never contains a full secret, so pasting it into an issue or chat
  cannot become a second leak.
- Placeholder values (`YOUR_API_KEY`, `<TOKEN>`, `changeme`, `example`, ...)
  are suppressed automatically; template files stay quiet.
- Default-excluded dirs: `.git`, `node_modules`, `__pycache__`, `venv`,
  `.venv`, `dist`, `build`. Binary files and files over 5 MB are skipped.

## Remediation workflow

1. Run the scan.
2. Rotate every CRITICAL credential at its provider console first — treat it
   as compromised.
3. Replace hardcoded values with environment variables or a secret manager.
4. Re-run until the scan reports zero findings.
5. If a secret was ever committed, clean git history too (`git filter-repo`
   or BFG), then rotate again.

## Privacy guarantee

Zero network calls: the engine imports Python standard library modules only
and never opens a connection — nothing you scan leaves your machine. It also
writes nothing to disk.

## Lite vs. full

This Lite edition is complete and self-contained for credential scanning. The
full **Secrets Hygiene Sweeper** adds: ~30 more rules (emails, phone numbers,
public/private IPs, tunnel domains, personal home paths, more vendors),
custom denylists for names and org-internal terms (the only reliable way to
catch CJK names), masked Markdown + JSON report export, `.sweeperignore` and
inline pragmas, `--fail-on` severity gating, and per-finding remediation
guides — maintained with model-regression re-testing.

## Disclaimer

This tool assists de-identification review; it does not guarantee that a
directory is free of sensitive data, and its output is not legal or
compliance advice. In principle, always pair automated scanning with human
review before publishing.

Guildshelf is not affiliated with Anthropic. Claude is a trademark of
Anthropic, used only to describe compatibility.
