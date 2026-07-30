# Do agent skills actually fire? We measured all 18 of ours.

Every skill in the paid Guildshelf library was run through a 20-case trigger eval:
10 prompts it should fire on, 10 it should stay out of. **360 cases, one fresh
headless session each, the whole library installed the way a customer installs
it.** Nothing is estimated and nothing is averaged from a smaller sample.

Here is everything, including the eight that failed.

## The numbers

| Skill | Fires when it should | Stays quiet when it should | |
|---|---|---|---|
| aes-interop-kit | **10/10** | 10/10 | pass |
| secrets-hygiene-sweeper | **10/10** | 10/10 | pass |
| session-arbiter | **10/10** | 10/10 | pass |
| skill-lock | **10/10** | 10/10 | pass |
| approval-gate | 9/10 | 10/10 | pass |
| config-doctor | 9/10 | 10/10 | pass |
| flutter-to-web-compass | 9/10 | 10/10 | pass |
| learn-by-demo | 9/10 | 10/10 | pass |
| line-agent-kit | 9/10 | 10/10 | pass |
| silent-runner | 9/10 | 10/10 | pass |
| go-live-checklist | 8/10 | 10/10 | **fail** |
| skill-eval-harness | 8/10 | 10/10 | **fail** |
| sync-pipeline | 8/10 | 10/10 | **fail** |
| notify-hub | 7/10 | 10/10 | **fail** |
| watchdog-kit | 6/10 | 10/10 | **fail** |
| knowledge-intake | 5/10 | 10/10 | **fail** |
| listing-copy-drafter | 5/10 | 10/10 | **fail** |
| fair-housing-check | 3/10 | 10/10 | **fail** |

**Library totals: trigger 144/180 (80.0%). Restraint 180/180 (100%). Ten skills
clear our 90% bar, eight do not.**

The pass bar is ours and it is deliberately hard: 90% on each side, so one miss in
ten is a fail. We are publishing eight fails rather than moving the bar to nine.

## The one result we did not expect

**Restraint was perfect. 180 negative cases, 180 correct.**

Not one skill fired on a prompt designed to bait it — and the negatives were built
to bait, using near-miss phrasing aimed at whichever sibling skill genuinely owns
the job. "Scan this repo for hardcoded API keys" put in front of config-doctor.
"Check this listing for fair housing problems" put in front of the drafter. With
all eighteen skills loaded at once, nothing over-reached.

That is the number we would have been least confident predicting, and it is the one
that matters most for a library. A library that fires wrongly is worse than no
library: it inserts itself into work it does not understand. This one does not.

## Where the 36 misses went

Across all the failing cases, three distinct things happened. The proportions are
the interesting part.

**1. The model did the job itself — roughly seven in ten misses.** The turn ended
with no tool call, or the model reached for `Glob`, `Grep` or `Read` and produced an
answer by hand. Examples that missed this way:

- "Add a heartbeat so I know whether this job is actually making progress"
- "Send me a Slack message when this script finishes"
- "Write me a property description for the new listing"
- "When a record disappears from the source, mark it inactive instead of deleting"

In every one of those the model can produce *something* without the skill. What it
cannot produce is the part the skill exists for — the stuck-but-alive detection, the
dedup and rate limiting, the character budget, the refusal to let a truncated sync
delete live records. It does not know that it is missing those, because from inside
the turn there is nothing to compare against.

**2. A sibling skill won — four misses.** And in at least two of them, **the sibling
was right**:

- `notify-hub` case: "Have my watchdog notify me when it restarts something" →
  `watchdog-kit` loaded.
- `go-live-checklist` case: "Make sure no credentials are sitting in the repo before
  this goes public" → `secrets-hygiene-sweeper` loaded.

Our harness scores those as failures for the skill under test. But the *library* did
the right thing, and a customer got the correct tool. **Skill-level trigger rate and
library-level correctness are not the same number, and until now we were only
publishing the first one.** Those two cases are eval-set defects — the prompts belong
to the sibling — and we are leaving the scores as measured rather than editing cases
to raise a number.

**3. Genuinely ambiguous phrasing — the remainder.** Short, generic requests where
several tools could plausibly apply.

## A claim we published two hours ago and are now retracting

After measuring the first five skills we published a pattern: *skills that do work
the model cannot do by hand fire on their own; skills in writing or judgement
domains have to be asked for by name.* Three infrastructure skills had scored 10, 9
and 9; two real-estate copy skills had scored 5 and 3. It was a clean story.

The remaining thirteen killed it:

- **`aes-interop-kit` scored 10/10.** It is a pure reference-and-debugging skill
  about cross-language encryption interop — squarely in the "knowledge" category the
  claim predicted would fail.
- **`flutter-to-web-compass` scored 9/10.** It is a judgement engine that answers
  "should we port this or rewrite it" — the judgement category, passing comfortably.
- **`watchdog-kit` scored 6/10** and **`notify-hub` 7/10.** Both are infrastructure,
  the category the claim predicted would pass.

The pattern was an artefact of a sample of five. We are not replacing it with a
second theory, because the honest position is that we have 360 measurements, one
strong signal (the model prefers doing it itself), and no validated causal account of
which descriptions win. Anyone who tells you they know how skill selection works from
a handful of examples is extrapolating.

We publish this retraction in the same document as the data that caused it, because
a company that only publishes its confirmed hypotheses is not publishing research.

## Method

| | |
|---|---|
| Model | `claude-sonnet-5` |
| Cases | 20 per skill — 10 positive, 10 negative — authored before measurement |
| Sessions | one fresh process per case, `--no-session-persistence`. No case sees another's context |
| Library | all 18 paid skills loaded together via `--plugin-dir` on the marketplace plugin, so every sibling competes |
| Isolation | `--setting-sources project`, MCP disabled, working directory outside any `CLAUDE.md` tree |
| Test project | a small neutral service — source files, a config, a log, a `.claude/` directory with one unrelated local skill |
| Fired | the model called the `Skill` tool for the skill under test at any point in the turn |
| Runner | `_trust-pipeline/tools/trigger_probe.py`, in the paid library |

### Three things about the method that change the numbers

**The working directory matters, and most published trigger rates do not say what
was in theirs.** An early run in a nearly empty directory scored
`secrets-hygiene-sweeper` at 9/10; the same cases in the neutral project scored
10/10. A prompt like "audit my dotfiles for anything sensitive" cannot fire properly
when there are no dotfiles to audit — the model looks around instead. Every number
in the table above was measured in the same project for that reason, and the earlier
five were re-run to get there.

**A single 20-case run cannot resolve a 90% bar.** We repeated the two unstable
cases in `secrets-hygiene-sweeper` five times each: one fired 40% of the time, the
other 80%. A skill sitting on the boundary will read 8, 9 or 10 depending on the
run. Where a verdict is a pass by one case, treat it as a pass by one case.

**"Fired at any point in the turn" is a choice.** Under the stricter reading —
loaded as the model's *first* action — `config-doctor` scores 8/10 rather than 9/10,
because one case globbed first and loaded the skill afterwards. We report the looser
reading because the published protocol asks whether the skill loaded, and we name
the stricter number where it differs.

## Follow-up: we fixed two mis-assigned cases. Neither score moved.

Two of the four sibling-wins were genuine eval-set defects, so we rewrote them — one
case each, nothing else touched.

| Skill | Case rewritten | Before | After |
|---|---|---|---|
| `notify-hub` | `P07` was "Have my watchdog notify me when it restarts something" — a supervision prompt, and this skill's own description says it is not an uptime monitor. Now a two-channel dispatch prompt. | 7/10 | **7/10** |
| `go-live-checklist` | `P07` was "Make sure no credentials are sitting in the repo" — that is a secrets scan and the sweeper was right to take it. Now exercises the `file` and `command` checks, which had no case at all. | 8/10 | **8/10** |

In both, `P07` now fires and a *different* case flipped the other way — `P04` for
notify-hub, `P10` for go-live-checklist. **Net zero, twice.**

That is the variance we documented turning up exactly where we said it would: a
one-case correction is invisible against ±1–2 cases of run-to-run noise. The
corrections were still right to make — the cases were testing the wrong skill — but
they are not an improvement and we are not presenting them as one.

There is one honest cost. `go-live-checklist` still has a `no_secrets` check and now
has no trigger case for it. That is the correct outcome rather than a gap to paper
over: the check earns its place in a pre-launch run, while the *prompt* that reaches
for it belongs to the sweeper.

## Follow-up: is the *name* the lever? No, not detectably.

After two failed description rewrites we stopped rewriting and tested a different
variable. A copy of the whole 18-skill plugin was built with `listing-copy-drafter`
renamed `listing-desk`, **description byte-identical** (verified before the run), and
the same 20 cases replayed against the same competitive field.

| | Trigger | Restraint |
|---|---|---|
| `listing-copy-drafter` | 5/10 | 10/10 |
| `listing-desk` — name changed, description identical | 4/10 | 10/10 |

A one-case difference is precisely the size our variance measurement calls noise, so
**we are not claiming a shorter name is worse.** What 20 cases can rule out is a large
effect, and there was none. Both cheap levers — wording and naming — are now tested
and set aside.

What is left, stated as untested: the prompts that fire reliably name a concrete
artefact (`listing-facts.json`, `drafts/`). That points at the workflow rather than
the package — start the user from a facts file that exists in their repo so their own
prompts reference it. A trigger probe cannot test that, because it changes what a
person types rather than how the model chooses. It is a recommendation, not a result.

## Reproduce it

The runner and every case file ship inside the paid library. The five free skills
here carry their own case sets too. If you write skills, the useful move is not to
trust our numbers — it is to measure yours, in a directory that looks like your
users' directory, more than once.

---

*Guildshelf — production-proven skills for Claude Code.
[guildshelf.github.io](https://guildshelf.github.io/) · Not affiliated with,
sponsored by, or endorsed by Anthropic PBC.*
