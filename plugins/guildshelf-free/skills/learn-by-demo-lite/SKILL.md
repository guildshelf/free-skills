---
name: learn-by-demo-lite
description: >
  Capture a real user demonstration of a web workflow (browser DevTools HAR
  export, or your agent runtime's own network reader) and turn it into a
  redacted endpoint draft, so automation is built from observed traffic
  instead of guessed APIs. Use when automating an internal tool, legacy SPA,
  or vendor portal that has no API docs; when guessed endpoints keep
  returning 401/403 or HTML instead of JSON; or when the user says "watch me
  do it once", "let me show you the steps", or "record what I click". Not
  for: services with documented public APIs (read the docs instead),
  bypassing CAPTCHAs, bot detection, or logins you are not authorized to
  use, scraping sites against their terms, generating UI test suites, or
  mobile-app reverse engineering. The Playwright capture harness,
  session-preservation (CDP attach), replay scaffold generator, and
  batch-hardening patterns are in the full Learn-by-Demo.
---

# Learn-by-Demo Lite

Stop letting your agent guess APIs. Capture one real demonstration — every
URL, header, and payload the workflow actually sends — then draft your
automation from observed traffic, not hallucinated endpoints.

## Why guessing fails

When an agent is told to automate a UI-driven system with no API docs, the
default failure mode is to *guess*: it invents an endpoint path, invents the
auth scheme, invents the body shape. Every wrong guess comes back as:

- **401 / 403** — the auth header is missing, malformed, or the wrong scheme.
- **HTML instead of JSON** — the guessed path doesn't exist, so the server
  returns a login page or a SPA shell.
- **Burned iterations** — each wrong guess is a full request/parse/retry
  loop converging on nothing.

A single real demonstration solves both halves at once: the **real endpoint,
method, and body shape**, and the **real authorization** as it was actually
sent. You capture facts, then replay facts.

## The Iron Rules

1. **Never hardcode an API or form flow before you have seen the real
   request.** No endpoint path, no header, no body schema goes into
   automation until it appeared in a capture.
2. **Prefer the user's already-logged-in browser session.** A second
   automated login can trigger single-device kick-out and invalidate the
   user's session. In this Lite edition that means: capture from the user's
   own browser window (DevTools), don't open a parallel login.
3. **Copy exactly what you captured** — endpoint, headers, auth, body
   schema — *then* parameterize. Reproduce first, generalize second.

## The capture workflow (Lite)

1. **Decide.** Does the task drive a UI, and are the exact endpoints
   unknown? If the target has documented public APIs, read the docs instead.
2. **Capture.** Two zero-install options:
   - **Your agent runtime's own network reader** — if the runtime you are in
     can read network requests from a browser it controls, arm it before the
     user clicks anything, then read the captured requests directly.
   - **Browser DevTools HAR export** — the user opens DevTools → Network,
     checks "Preserve log", performs the workflow slowly (pausing per step),
     then right-clicks → "Save all as HAR".
3. **Draft.** Feed the capture to the draft tool:

   ```
   python scripts/har_draft.py capture.har
   ```

   You get a redacted Markdown draft per endpoint: method, URL template
   (volatile ids normalized to `{id}`/`{uuid}`), auth type, query
   parameters, request-body field names, and statuses seen.
4. **Build replay from the draft.** Reproduce one call exactly as captured
   (same headers, same body shape) and confirm it returns the same result
   the user saw. Only then parameterize.
5. **Persist.** Write the endpoint/field/flow knowledge into a project-level
   skill or memory so the next run needs no demonstration.

Try it on the bundled synthetic capture:
`python scripts/har_draft.py fixtures/sample_capture.har`

## Handling captured secrets

Captures contain **live credentials**. Discipline is non-negotiable:

- `har_draft.py` **always redacts** Authorization, Cookie, API-key headers,
  and token-ish query parameters. There is no off switch.
- **Never commit a raw HAR.** Keep captures out of version control
  (add them to `.gitignore`) and delete them when done.
- **Replay reads tokens from an environment variable**, never a literal in
  the script.
- **Never paste a raw capture into a prompt, issue, or chat.** Draft first.

## Anti-patterns

- **Guessed-endpoint loop.** Inventing `/api/.../records` and its body,
  getting 401s and HTML, and retrying with another guess. Fix: capture the
  real request once.
- **Second-login kick-out.** Spinning up a separate automated login "to
  test", which invalidates the user's live session. Fix: capture from the
  user's own window.
- **Committing a live token.** Saving a raw HAR with a valid
  `Authorization` header into the repo. Fix: draft (redacted) goes in the
  repo; the HAR does not.

## Lite vs. full

This Lite edition covers the methodology plus HAR-to-draft. The full
**Learn-by-Demo** adds: a Playwright capture harness that attaches to the
user's already-logged-in browser over CDP (JSONL + HAR output),
session-preservation recipes (storage state, persistent profiles, the three
ways around single-device kick-out), a machine-readable endpoint-spec
format, a replay-script scaffold generator (tokens via env var), and
batch-hardening patterns (pagination, token-expiry refresh, polite rate
pacing, baseline verification) — with a worked end-to-end example against a
public demo site.

## Responsible use

Only automate systems you are authorized to use, and respect the target
system's terms of service. This skill does not help bypass authentication,
CAPTCHAs, bot detection, or access controls.

*Not affiliated with Anthropic; Claude is a trademark of Anthropic,
referenced only to describe compatibility.*
