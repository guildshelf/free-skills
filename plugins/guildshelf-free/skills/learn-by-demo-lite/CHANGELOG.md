# Changelog

All notable changes to Learn-by-Demo Lite are documented here.
This project adheres to [Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-07-18

### Added

- Initial open-source release of **Learn-by-Demo Lite** (Apache-2.0), the
  free edition of the Guildshelf Learn-by-Demo skill.
- `SKILL.md` — capture-from-demonstration methodology: why guessing fails,
  the three Iron Rules, the 5-step Lite capture workflow (runtime network
  reader or DevTools HAR export → draft → exact reproduce → parameterize →
  persist), secrets discipline, and anti-patterns.
- `scripts/har_draft.py` — stdlib-only HAR-to-draft tool. Groups API-looking
  traffic into endpoints (URL templates with `{id}`/`{uuid}` normalization),
  detects the auth type, lists query params / body field names / statuses,
  and emits a Markdown draft. Credentials are always redacted (no off
  switch). `--host` and `--all` filters; exit codes 0/2.
- `fixtures/sample_capture.har` — synthetic 4-entry capture (fake
  example-only tokens) demonstrating login, an authenticated fetch, a 401
  without the session, and a filtered static asset.
- `eval/cases.md` — 20 trigger / non-trigger evaluation cases.
- `LICENSE.txt` — Apache License 2.0.

### Notes

- Lite scope: capture + draft only. Playwright/CDP capture harness,
  session-preservation recipes, machine-readable specs, replay scaffolding,
  and batch-hardening patterns are in the full Learn-by-Demo.
