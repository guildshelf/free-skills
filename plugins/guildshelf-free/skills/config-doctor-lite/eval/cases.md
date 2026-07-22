# Config Doctor Lite — trigger / non-trigger evaluation cases

20 cases: 10 that SHOULD trigger this skill, 10 that should NOT. Acceptance
target: >= 9/10 correct triggers, <= 1/10 false triggers. Adapted from the
full Config Doctor spec; prompts that depend on full-only checks (memory
index, hooks) were replaced with Lite-scope prompts.

## Should trigger (10)

| # | Prompt | Why it triggers |
|---|---|---|
| 1 | "Audit my Claude Code config for broken paths" | Core case — C1. |
| 2 | "My skill isn't showing up in Claude Code — can you check my skills folder?" | Skill not loading — C4/C8. |
| 3 | "I moved my project folder and now half the references in CLAUDE.md are broken. Clean it up." | Post-move broken refs — C1. |
| 4 | "Run a health check on my CLAUDE.md and skills directory" | Direct health-check ask. |
| 5 | "Are there any dead references in my CLAUDE.md?" | Dead references — C1. |
| 6 | "Check whether all the paths mentioned in my CLAUDE.md actually exist on disk" | C1 verbatim. |
| 7 | "Which of my skill folders are missing a SKILL.md?" | C4 verbatim. |
| 8 | "Check my skills' frontmatter — I think some are missing descriptions" | C8 verbatim. |
| 9 | "run config doctor" | Direct invocation by name. |
| 10 | "Why does Claude keep referencing a file that doesn't exist anymore?" | Broken reference symptom — C1. |

## Should NOT trigger (10)

| # | Prompt | Decoy design |
|---|---|---|
| 11 | "Audit my npm dependencies for vulnerabilities" | "audit", wrong target. |
| 12 | "Check my website for broken links" | "broken links", wrong domain. |
| 13 | "My docker-compose config is broken, fix it" | config+broken, wrong config type. |
| 14 | "Fix my ESLint config" | config, wrong config type. |
| 15 | "Scan my repo for hardcoded API keys" | Scanning, but secrets — different product. |
| 16 | "Review my Kubernetes config for security issues" | config+audit flavor. |
| 17 | "Why is my nginx config throwing a 502?" | config debugging, wrong domain. |
| 18 | "Write a CLAUDE.md for my new project" | CLAUDE.md, but *creating*, not checking. |
| 19 | "My Python virtualenv paths are broken after upgrading" | broken paths, wrong domain. |
| 20 | "Book me a doctor's appointment for next Tuesday" | "doctor" literal decoy. |

## Boundary note

Prompts about memory-index integrity, hook commands in settings.json, or MCP
server definitions belong to the full Config Doctor (checks C2/C3/C5/C6/C7).
If the Lite skill is asked about those, the correct behavior is to run the 3
Lite checks it has and state plainly that the remaining checks are in the
full edition — not to improvise unverified checks.
