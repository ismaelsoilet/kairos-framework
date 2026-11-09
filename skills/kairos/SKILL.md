---
name: kairos
description: "Spec-driven delivery with an anti-drift gate. Decides whether a ticket justifies a spec, drafts the eight-item spec that measurably merges better, then verifies the delivered diff actually matches it. Use for features or multi-file changes; skip for one-file bugfixes, where the measured gain is zero."
---

# KAIROS

Two failures this prevents:

1. **Spec theatre.** Writing a 128-line spec that nobody follows. In a controlled
   benchmark of 50 production tickets, 7.9% of merged spec-arm tickets did not
   match their own spec.
2. **False completion.** "Done, tests pass" with no diff inspection. In an RCT of
   experienced developers, AI made them 19% slower while they believed they were
   20% faster.

Everything here is measured, and the numbers come from
`docs/EVIDENCE.md`. Where there is no evidence, this skill says so.

---

## Step 0 — Should this ticket have a spec?

Run the fit test before anything else. On bug-fix, refactor and test-writing
tickets the benchmark found **0 percentage points** of gain while the spec phase
cost ~18 minutes and ~35% of the tokens.

```bash
kairos fit --touches 5 --criteria 6 --changes-schema-or-api --crosses-boundary
```

Write a spec when **3 or more** are true:

| Statement | Why it counts |
| :--- | :--- |
| touches 3+ files | the measured threshold where the spec paid back |
| 4+ acceptance criteria | more surface for a misunderstanding |
| crosses a module/service/repo boundary | context that has to survive a session |
| alters a data schema or public API | rework is expensive |
| more than one agent or engineer | the spec is the shared memory |
| regulated or audited code | the spec is the record |

**If fewer than 3:** give the agent the ticket text and the acceptance criteria,
then review the diff. Do not run the rest of this skill. Skipping the ceremony is
the correct output, not a shortcut.

---

## Step 1 — Draft the spec

```bash
kairos spec <name>
```

The generated `specs.md` already has all eight sections. Fill them; do not delete
one without a one-line reason. Sections, and why each is there:

| Section | What breaks without it |
| :--- | :--- |
| **Goal** | the agent optimises for the wrong outcome |
| **Scope** | work expands into neighbours |
| **Inputs and outputs** | types get guessed |
| **Data changes** | migrations are forgotten |
| **Edge cases** | only the happy path is built |
| **Acceptance tests** | drift becomes undetectable |
| **Constraints** | a dependency appears from nowhere |
| **No-change list** | unrelated files get rewritten |

Specs covering **6 or more of 8** merged 89.3% of the time; fewer merged 60.0%.

Keep it under ~130 lines. A spec a senior engineer cannot review in ten minutes
is a spec they will rubber-stamp, which is worse than no spec.

### The no-change list is the load-bearing section

It is the only section the gate turns into a hard block. Be specific and literal:

```markdown
## No-change list
- `src/billing/legacy.py`
- `api/v1/**`
```

### This is a back end, not a framework

Do not replace your spec tool with this. Use **one** spec tool — OpenSpec is the
measured best choice (42/50 merged, 2.4% drift, fastest spec phase) — and put
this gate behind it.

OpenSpec already has `/opsx:verify`. Read that first. The gate adds two things it
does not do:

| | `/opsx:verify` | `kairos gate` |
| :--- | :--- | :--- |
| Output | a report | **exit code** (0 = READY) |
| Blocking | advisory, "archive retains its own checks" | fails the build |
| No-change list | not supported | blocks on it |
| Spec completeness floor | not checked | blocks below 6/8 |

Use both if you use both. If `/opsx:verify` later blocks builds and checks
invariants, delete this gate.

`kairos gate` parses KAIROS, EGM, OpenSpec and Spec Kit layouts, so whichever you
already write is probably fine. For OpenSpec it reads `proposal.md`, `design.md`
and the delta `spec.md` together — a delta spec alone scores 3/8, which is the
format doing less, not the author doing worse.

---

## Step 2 — Get the spec attacked before coding

Spawn review in a **fresh context**. A reviewer in your conversation inherits
your assumptions and will approve them.

If your harness supports subagents, dispatch one with only the spec file and the
paths it references. If it does not, start a new session and paste the spec. A
review in the same context is not a review.

Ask three questions, in this order (this is the EGM Goldfish protocol, which is
public and Apache-2.0):

1. **Comprehension** — restate the design. If the reviewer cannot, the document
   is ambiguous, not the reviewer.
2. **Adversarial** — what edge case, hidden dependency or logical gap is missing?
3. **Readiness** — are the file paths, data structures and signatures present and
   unambiguous enough to implement without decisions?

Fix the spec, not the reviewer.

---

## Step 3 — Build

Normal work. The only rules that matter for what comes next:

- Work on a branch, so `kairos gate --base main` has something to compare.
- Touch the files the spec named. If you must touch another one, add it to the
  spec first — that is the whole point of a spec.
- Do not edit the acceptance criteria to match what you built. That is the fraud
  the gate is looking for.

---

## Step 4 — Gate

```bash
kairos gate --spec .kairos/changes/<id>/specs.md --base main
```

Exit code is `0` only on READY, so it drops straight into a pre-push hook or CI.

| Verdict | Meaning | What to do |
| :--- | :--- | :--- |
| **READY** | spec complete, diff consistent | ship |
| **REPAIR** | scope drift, unmatched criteria, or a fraud pattern | fix, or amend the spec deliberately |
| **BLOCKED** | spec too weak to trust, or a no-change violation | stop |

The gate checks:

- **spec completeness** below 6/8 → BLOCKED, because a weak spec makes
  "it matches the spec" meaningless
- **no-change list violated** → BLOCKED
- **files touched that the spec never named** → REPAIR
- **acceptance criteria with no test in the diff** → REPAIR
- **test deletion / weakened tests** → REPAIR (only rules with measured non-zero
  precision run by default)

### What the gate cannot do

Be explicit with whoever reads the output:

- It compares words, not meaning. A test named after a criterion but asserting
  nothing passes the drift check.
- It cannot tell an intentional deletion from a fraudulent one.
- Four of the scanner's rules are **off by default** because their precision on
  real merged PRs was 0-17%. Do not re-enable them and then complain about noise.
- It does not run your tests. Run them.

---

## Step 5 — Report

Say what happened, in this order:

1. What changed, in one sentence.
2. Gate verdict, quoted from the command output — not paraphrased.
3. What the gate did **not** check.

If the gate said REPAIR and you shipped anyway, say so and why. An honest REPAIR
that was overridden is worth more than a fabricated READY.

---

## The two rules that never turn off

1. **Claims are not evidence.** A diff, a command output, and a gate verdict are.
   Nothing else counts.
2. **Self-report is the least reliable signal available.** The developers in the
   RCT were confident and wrong by 39 percentage points. When you feel certain
   the work is done, that is the moment to run the check.
