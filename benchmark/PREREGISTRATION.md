# Pre-registration — KAIROS vs baseline, token cost of an agentic coding cycle

**Status:** written 2026-11-08, **before any data collection**.
**Data collected so far: none.** This file exists so the hypotheses and the
decision rule cannot be adjusted after seeing results.

If a later report contradicts this file, this file wins on what was predicted;
the report wins on what was observed. Both must be published.

---

## 1. Question

Does imposing the KAIROS process (dial → spec → worktree → TDD → mutation →
audit) on an AI coding agent reduce the **total tokens** needed to reach a
correct, reviewed implementation, compared to letting the agent work freely?

The retracted v1.1.0 claim was that it saves 19–85%. That claim had no
experiment behind it. This is the experiment.

---

## 2. Hypotheses

**H1 (the project's prior):** the governed arm requires fewer active tokens
(input + output) across the whole cycle, because it front-loads specification
and avoids a repair cycle.

**H0 (the one that can win):** the governed arm costs the same or more. This is
a live possibility and not a failure of the exercise:

- the process itself costs tokens (spec, critic, mutation runs, audit);
- a competent agent may solve the task in one pass without governance;
- governance may improve *quality* while costing *more*, which would be a
  legitimate finding and a very different product claim.

**H2 (secondary):** any token advantage comes from the extra information in the
prompt, not from the process. This is tested by the "hint" control arm below.
If H2 holds, KAIROS's value is in the prompt discipline, not the tooling.

---

## 3. Arms

Three arms, **identical task text, verbatim**, differing only in process
instructions. No arm receives the solution.

| Arm | What the agent is told |
| :--- | :--- |
| **A — free** | The task. Nothing else. |
| **B — hint** | The task, plus: "Pay attention to concurrent access and data integrity." |
| **C — kairos** | The task, plus the KAIROS pipeline: classify, write delta spec, work in a worktree, failing test first, mutation check, audit before declaring done. |

**Arm B is mandatory.** Without it, a result in favour of C cannot be
distinguished from "a warning about the hazard helps". The retracted benchmark
failed exactly here: only the KAIROS arm was told about the race condition.

**Explicitly forbidden in all arms:** naming the mechanism (`AsyncMutex`,
`lock`, `queue`, `serialize`), or describing how to detect the defect. Arm B may
say "be careful about concurrency"; it may not say what to do about it.

---

## 4. Tasks

Two tasks, chosen before results, for different risk profiles:

- **T1 (high risk):** implement a wallet with withdraw and deposit over an
  async persistence boundary. Acceptance: 60 concurrent withdrawals of 10 from
  500 leave balance 0 with exactly 50 successes and 10 rejections, and the
  balance never goes negative.
- **T2 (low risk):** add a coupon rule to an existing pricing function with an
  existing test suite. Acceptance: new behaviour correct, existing tests still
  pass, no change to unrelated behaviour.

T2 exists to test the *other* direction: governance should be cheap or
neutral on low-risk work. If KAIROS loses on T2, the Elastic Dial is not doing
its job.

---

## 5. Measurements

**Primary:** active tokens (input + output) for the full cycle until the task is
accepted or abandoned. Taken from provider-reported usage, not from counting
characters locally.

**Secondary:** cache-read tokens, cache-write tokens, USD cost, wall-clock,
number of human interventions, and blind-judge quality score.

**A cycle ends when:** the acceptance check passes, or the agent declares
completion, or a token/step budget is exhausted. A cycle that ends without
passing is scored as a failure, and its tokens still count. Abandoning a failed
attempt must cost something, otherwise failures look cheap.

---

## 6. Design and analysis

- **n = 5 independent runs per arm per task** = 30 cycles minimum.
- Same model, same version, temperature fixed and recorded, fresh context per run.
- Order randomised to avoid warm-cache bias; the arm assignment is recorded
  before each run.
- Report **mean, median, and 95% bootstrap CI** of the per-run difference.
- **Decision rule, fixed now:** if the 95% CI of the difference includes zero,
  the published conclusion is **"not demonstrated"**. No spinning a
  non-significant difference into a direction.
- Report T1 and T2 separately. Do not pool them into a headline number. A single
  aggregate percentage is what produced the retraction.

---

## 7. Quality, judged blind

Acceptance tests are objective; quality beyond them needs a judge. A judge
model receives the diff with all arm identifiers stripped, and a rubric written
before any run is seen:

1. Does the implementation satisfy the acceptance criteria?
2. Are there tests that would fail if the implementation were wrong?
3. Is there silent error handling or dead code?
4. Is the diff scoped to the task?

The judge's rubric-compliance is itself reported. The judge is not told which arm
produced which diff, and the mapping is revealed only after scoring.

---

## 8. What would make this invalid

Recorded in advance so it is hard to rationalise later:

- Arms receiving different task text, in any wording.
- The governed arm receiving the mechanism name.
- Reporting only successful runs.
- Reporting a pooled number across T1 and T2.
- Reporting a percentage without the raw per-run values.
- Any change to H1/H0 or the decision rule after seeing data.

If any of these happen, the result is not a result.

---

## 9. Current status

**Blocked.** No provider credentials are configured in this environment, and no
budget has been authorised. No run has been performed. Nothing in this
repository should be read as a result of this protocol until a report exists
that cites this file and publishes the raw per-run table.
