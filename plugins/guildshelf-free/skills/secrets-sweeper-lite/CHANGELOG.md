# Changelog

All notable changes to Secrets Sweeper Lite are documented here.
This project adheres to [Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-07-18

### Added

- Initial open-source release of **Secrets Sweeper Lite** (Apache-2.0), the
  free edition of the Guildshelf Secrets Hygiene Sweeper.
- `scripts/sweeper_lite.py` — single-file, stdlib-only offline scanner with
  the 10 highest-impact credential rules: private-key-block,
  aws-access-key-id, github-token, openai-key, anthropic-key, google-api-key,
  slack-token, stripe-live-secret-key, jwt, generic-credential-assignment
  (entropy-checked).
- Masked terminal output (first 4 + last 2 characters kept), placeholder
  suppression, default directory exclusions, binary/oversize skipping.
- Exit codes `0` clean / `1` findings / `2` error for CI use.
- `SKILL.md` with triggering description (trigger + not-for cases),
  `eval/cases.md` (20 trigger / non-trigger cases), `README.md`,
  `LICENSE.txt` (Apache-2.0).

### Notes

- Lite scope: credentials only, terminal output only. PII/IP/tunnel/path
  rules, custom denylists, and Markdown/JSON report export are in the full
  Secrets Hygiene Sweeper.
