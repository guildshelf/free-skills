# trigger-probe

**Measure whether your Claude Code skill actually fires.** Apache-2.0, Python
standard library only, one file.

A skill description is a bet: that when a user phrases a request their own way, the
model decides to load your package. Nothing about writing a good description tells
you whether you won that bet. This runs the experiment — fresh session per case,
prompt passed through verbatim, and it records which skill the model actually chose.

We built it to measure our own library and published the numbers, including the eight
skills that failed. **[The report is here](../../EVAL-REPORT.md)** — 18 skills, 360
cases. This is the tool that produced it.

## Use it

```bash
# skills from your project's .claude/skills
python trigger_probe.py cases.md --slug my-skill

# a whole plugin, which is how customers actually have it installed
python trigger_probe.py cases.md --slug my-skill --plugin-dir path/to/plugins/my-plugin

# artefacts you can commit
python trigger_probe.py cases.md --slug my-skill \
    --plugin-dir ../plugins/my-plugin \
    --lab ~/work/a-realistic-project \
    --results results.json --card scorecard.md
```

Exit `0` both sides at or above the bar · `1` below it, or cases left unrun · `2`
could not run. So it works as a release gate.

## The cases file

Two headings, and either a numbered list or a markdown table under each. Both parse:

```markdown
## Should trigger

1. "Scan this repo for hardcoded secrets before I publish."
2. "Check whether I leaked an API key in here."

## Should NOT trigger

| ID | Prompt | Why it should lose |
|----|--------|--------------------|
| N1 | Rotate my AWS access keys | remediation, not scanning |
| N2 | Set up Vault for our team secrets | runtime secret management |
```

Write the negatives as **near misses aimed at whichever skill genuinely owns the
job**, not as unrelated prompts. "Book me a doctor's appointment" is a free pass; "scan
this repo for hardcoded keys" put in front of a config linter is a real test.

## Useful flags

| Flag | Why |
|---|---|
| `--lab DIR` | run each session in a directory that looks like your users'. This changes results more than anything else here |
| `--repeat N` | run each case N times. Boundary cases are stochastic; this shows you by how much |
| `--first-action-only` | stricter: count only skills loaded as the model's *first* action |
| `--only P04,P07` | re-run just the cases you are investigating |
| `--setting-sources project` | default. Keeps your own user-level skills out of the run, where they would otherwise win cases your users would give to you |
| `--budget 0.15` | hard USD cap per case |

## Three things we learned the hard way

**Your working directory changes the answer.** The same cases scored 9/10 in a nearly
empty directory and 10/10 in a realistic project. "Audit my dotfiles for anything
sensitive" cannot fire properly when there are no dotfiles — the model looks around
instead of loading anything. Measure somewhere realistic, and say which directory you
used when you publish a number. Most published trigger rates do not.

**One 20-case run cannot resolve a 90% bar.** We repeated two of our boundary cases
five times each: one fired 40% of the time, the other 80%. A skill on the boundary
reads 8, 9 or 10 depending on the run. If your verdict is a pass by one case, it is a
pass by one case — and if you "improved" a skill by one case, you have measured
nothing. We fixed two genuinely mis-assigned cases in our own set and both scores came
out identical, because another case flipped each time.

**Install the whole library, not the skill alone.** With siblings absent the negative
side is meaningless — there is nothing for a near-miss prompt to lose to. And when a
sibling *does* win, that is often correct: two of our "failures" were the right skill
loading for a prompt we had filed under the wrong one. **Your skill's trigger rate and
your library's correctness are different numbers.**

## What it does not tell you

Whether the skill is any good once loaded. This measures the loading decision and
nothing else. A skill can score 10/10 and still give bad advice.

It also cannot test the one lever we think is left. Across our library, roughly seven
in ten misses were the model simply doing the job itself — ending the turn with no tool
call, or reaching for `Glob`/`Grep`/`Read`. We tried the two fixes a probe *can* test:
rewriting descriptions twice, and renaming a skill with the description held
byte-identical. Neither moved the number. What did correlate with firing was prompts
that name a concrete file — so the remaining idea is about the user's workflow rather
than your metadata, and a probe cannot measure what a person chooses to type.

## Requirements

`claude` on PATH, and Python 3.9+. Nothing else — no pip install, no config file.

---

Built by [Guildshelf](https://guildshelf.github.io/). Apache-2.0: use it, fork it,
ship it in your own release gate. If you publish numbers from it, publish the working
directory and the model too — that is the difference between a measurement and a
marketing claim.
