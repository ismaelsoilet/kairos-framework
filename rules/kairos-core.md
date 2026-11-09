# KAIROS Core Directives

You are operating under KAIROS. This file is what the agent reads. It describes
only what exists; anything not listed here was removed in v1.3 and is in
`docs/archive/`.

## 1. What this is

Four checks that a model cannot do by reasoning:

| Command | Question |
| :--- | :--- |
| `kairos fit` | should this ticket have a spec at all? |
| `kairos brainstorm` | what did we reject, and what would prove this wrong? |
| `kairos gate` | does the delivered diff match the approved spec? |
| `kairos audit` | did the change weaken a test? |

There is no classifier, no lifecycle, no telemetry header, no worktree, no
subagent roster. Do not invent them, and do not run commands that are not in
this list.

---

## 2. The five iron laws

1. **No production code without a failing test.** If you did not watch it fail,
   you do not know what it tests. Code written before a test must be discarded.
2. **No guesswork in debugging.** Reproduce the defect in a minimal test before
   touching production code.
3. **Ground truth is `git diff` and command output.** A report is a set of
   claims. "Tests pass" is a claim until the exit code is in front of someone.
4. **Hunt the six classic frauds** — weakened checks, false completion, scope
   creep, unauthorized action, spec betrayal, debris.
5. **Declare the invariants.** A spec must say what must not change, or there is
   nothing to check the diff against.

Law 3 is the one this project violated most thoroughly. It is why `gate` exists
and why `--verify` runs the command instead of believing the summary.

---

## 3. When to write a spec

Run the fit test first. On bug-fix, refactor and test-writing tickets the
measured gain was **0 percentage points** while the spec phase cost about 18
minutes and 35% of the tokens.

```bash
kairos fit --touches 4 --criteria 5 --crosses-boundary
```

Write a spec when **three or more** are true:

- the change touches three or more files
- it has four or more acceptance criteria
- it crosses a module, service or repository boundary
- it alters a data schema or a public API
- more than one agent or engineer will work on it
- the code is regulated or audited

Fewer than three: give the agent the ticket text and the acceptance criteria,
then review the diff. Skipping the ceremony is the correct output.

---

## 4. The spec must be complete enough to check against

`kairos spec` generates eight sections. Do not delete one without a one-line
reason. Specs covering six or more merged 89.3% of the time; fewer merged 60.0%.

| Section | What breaks without it |
| :--- | :--- |
| Goal | the agent optimises for the wrong outcome |
| Scope | work expands into neighbours |
| Inputs and outputs | types get guessed |
| Data changes | migrations are forgotten |
| Edge cases | only the happy path is built |
| Acceptance tests | drift becomes undetectable |
| Constraints | a dependency appears from nowhere |
| No-change list | unrelated files get rewritten |

The no-change list is the only section that becomes a hard block. Be literal:
`src/billing/legacy.py`, `api/v1/**`.

---

## 5. Before coding

`kairos brainstorm --check` refuses a brief with fewer than three alternatives,
an alternative with no rejection reason, or no "what would make this wrong"
section. That is deliberate: a spec that commits to one design without recording
what it rejected is not a decision.

If your harness can spawn a fresh-context reviewer, use one to attack the spec
before implementation. A reviewer inside the same conversation inherits its blind
spots. If you cannot spawn one, say so — do not pretend a same-context review is
a review.

---

## 6. Before declaring done

```bash
kairos gate --spec <path> --base main --verify "<test command>"
```

`0` is READY. Anything else is not.

| Verdict | Meaning |
| :--- | :--- |
| **READY** | spec complete, diff consistent, the command ran and passed |
| **REPAIR** | scope drift, unmatched criteria, debris, or a fraud pattern |
| **BLOCKED** | spec too weak to trust, a no-change violation, or the command failed |

Report the verdict by quoting the command output. Do not paraphrase it.

**If the gate says REPAIR and you ship anyway, say so and say why.** An honest
REPAIR that was overridden is worth more than a fabricated READY.

---

## 7. What the gate cannot check

State these limits whenever you report a verdict:

- It compares words, not meaning. A test named after a criterion but asserting
  nothing passes.
- It does not run the tests unless `--verify` is given.
- It cannot tell an intentional deletion from a fraudulent one.
- Three scanner rules are off by default because their measured precision on real
  merged pull requests was 0–17%. Do not enable them and then complain about
  noise.
- `gate` reads English and Portuguese specs. Other languages score low, and that
  is a limitation of the checker, not a judgment on the spec.

A green gate is not proof of correctness. It is proof that nobody weakened the
tests, drifted from the spec, or left a debugger in the diff — which is a
different and smaller claim.

---

## 8. Destructive actions

Never push, deploy, publish, drop a table, or delete shared data without explicit
authorization. `kairos gate` reports `outward_command` findings as REPAIR for
exactly this reason: adding a deploy script is often correct, but a human has to
see it first.
