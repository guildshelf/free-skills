# Guildshelf — Free Skills

Five production-grade skills for **Claude Code**, free and open-source (Apache-2.0).
They run in *your* environment on *your* accounts — we never see your keys or data.

## Install

```
/plugin marketplace add guildshelf/free-skills
```

## Also free: the tool we measured ourselves with

**[`tools/trigger-probe`](tools/trigger-probe/)** — one Python file, Apache-2.0, no
dependencies. Point it at a cases file and it tells you whether your skill actually
loads: fresh session per case, whole plugin installed, prompt passed through verbatim.

```bash
python tools/trigger-probe/trigger_probe.py cases.md --slug my-skill     --plugin-dir path/to/plugins/my-plugin --card scorecard.md
```

It is the tool that produced [EVAL-REPORT.md](EVAL-REPORT.md), including the eight of
our own skills that failed. Its README documents the three things that changed our
numbers — the working directory matters, one 20-case run cannot resolve a 90% bar, and
a sibling skill winning is often correct rather than a failure.

## What's inside

| Skill | What it does |
|---|---|
| **secrets-sweeper-lite** | Catch hardcoded keys, IPs and personal data before they ship in a skill |
| **config-doctor-lite** | Find dead paths and stale references across your CLAUDE.md, memory and skills |
| **learn-by-demo-lite** | Capture real network requests from a demo, then build automation on facts |
| **silent-runner-lite** | Keep background jobs running without console windows stealing focus (Windows) |
| **aes-cheatsheet** | Cross-language OpenSSL "Salted__" AES interop, one reference page |

## The full library — 16 skills, three lines

Deeper pipelines, extracted from workflows that ran a real business, then
genericized and hardened. Every release **scanned, signed, eval-tested, and
re-verified within 48h of every model update**.

- **TRUST** — pin installed skills to content hashes and report drift · measure
  whether a skill actually fires · score a claim before it enters memory · catch
  secrets and dead config before they ship
- **OPS** — restart a job when it crashes *and* when it is alive but stuck ·
  deliver the alert with dedup and rate limiting · verify DNS, ports, health and
  certificates before a launch · stop concurrent agents corrupting each other
- **DATA** — put a human yes between what an agent extracted and your database,
  on an append-only trail · mirror upstream data without letting a truncated
  "full" sync delete real records

Every skill ships with its own tests, an eval case set, a changelog, and an
honest list of what it does **not** do.

## Does any of this actually fire?

We measured all 18 paid skills: 20 trigger cases each, 360 cases, one fresh session
per case, the whole library installed the way a customer installs it.

**Trigger 144/180. Restraint 180/180 — not one skill fired on a prompt built to bait
it. Ten skills clear our 90% bar and eight do not, the worst at 3/10.**

All eight failures are published, with the fixes that did not work, plus a pattern we
published from the first five skills and then retracted when the other thirteen
refuted it. → **[EVAL-REPORT.md](EVAL-REPORT.md)**

## Pricing

| | Price | Cap |
|---|---|---|
| **Founding Annual** | **US$199/year**, held at that rate while you stay | first **150** |
| **Founding Lifetime** | **US$499** once, no renewal | first **50** |
| Team | US$99/month, 5 seats (+US$15/seat) | — |
| Pro (list price after the caps) | US$29/month or US$290/year | — |
| **Done-with-you setup** | **US$399** once — guided setup, one skill built to your spec, a runbook | 3 this week, 10 total |

**The checkout is not open yet, and we are not going to pretend otherwise.**
Reserving costs nothing and takes about a minute — it opens a thread here, we
reply with a payment link the day the checkout goes live, and you decide then.
The caps are counted in the open: every reservation is visible under the
[`founding-seat`](../../issues?q=is%3Aissue+label%3Afounding-seat) label, so you
can count them yourself.

| | |
|---|---|
| 🔖 **Hold a founding rate** | [Reserve a seat →](../../issues/new?template=01-founding-seat.yml) |
| 🛠 **Get it set up for you** | [Start a setup thread →](../../issues/new?template=02-setup-service.yml) |
| 💡 **Something missing?** | [Request a skill, free →](../../issues/new?template=03-skill-request.yml) |

Full detail and the four commitments: **[guildshelf.github.io](https://guildshelf.github.io/)**

## License

Apache-2.0. Guildshelf is not affiliated with, sponsored by, or endorsed by Anthropic.
"Claude" and "Claude Code" are trademarks of Anthropic, used only to describe compatibility.
