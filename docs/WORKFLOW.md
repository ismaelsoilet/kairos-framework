# The cycle: OpenSpec + KAIROS, start to finish

One spec tool, one verification step, no other frameworks. Verified end to end
against OpenSpec v1.x on a real project, not on fixtures.

```text
1. kairos fit              do we need a spec at all?
2. openspec new change     the plan lives in openspec/changes/<name>/
3. fill proposal           why, what changes, capabilities, impact
4. fill specs/*/spec.md    Requirement: + Scenario: blocks
5. fill design.md          decisions, edge cases, files to touch
6. kairos brainstorm       the alternatives you rejected
7. (fresh-context review)  attack the spec before coding
8. implement + test
9. openspec validate       the change is structurally valid
10. kairos gate            does the diff match the spec, and do the tests pass
11. openspec archive       fold the delta into the living spec
```

Steps 1, 6, 7 and 10 are KAIROS. Everything else is OpenSpec. Neither replaces
the other.

---

## Step 1 — should this have a spec?

```bash
kairos fit --touches 5 --criteria 6 --changes-schema-or-api --crosses-boundary
```

On bug-fix, refactor and test-writing tickets the measured gain was **0
percentage points** while the spec phase cost ~18 minutes and ~35% of the tokens.
If the answer is NO_SPEC, skip to step 8 and give the agent the ticket text plus
the acceptance criteria.

---

## Steps 2–5 — the OpenSpec artefacts

```bash
openspec new change add-rate-limit
openspec instructions proposal --change add-rate-limit   # tells you the sections
```

OpenSpec writes `openspec/changes/<name>/`. You fill:

| File | What goes in it | Why KAIROS cares |
| :--- | :--- | :--- |
| `proposal.md` | Why, What Changes, Capabilities, Impact | supplies goal, scope, impact |
| `specs/<cap>/spec.md` | `### Requirement:` + `#### Scenario:` blocks | each scenario becomes an acceptance criterion |
| `design.md` | decisions, edge cases, **files to touch** | supplies edge cases and the declared file list |

**The file list in `design.md` is load-bearing.** `kairos gate` compares it with
the diff and reports anything else as scope drift. If you do not list a file you
intend to touch, the gate will flag it — which is the check working, not a bug.

**Several scenarios per requirement are counted separately.** A requirement with
three scenarios is three things to verify. An earlier version of the gate kept
only the first and let two thirds of the spec go unchecked.

---

## Step 6 — the alternatives

```bash
kairos brainstorm --new add-rate-limit
kairos brainstorm --check brainstorm.md
```

Refuses fewer than three alternatives, an alternative with no rejection reason,
or no "what would make this wrong" section. OpenSpec's `explore` is deliberately
non-linear with no mandatory artifact, so this is the one thing it does not
record.

Keep `brainstorm.md` next to `design.md`. A fresh-context reviewer should read
both and treat a rejected option that reappeared in the design as a finding.

---

## Step 7 — attack the spec before coding

Spawn `agents/kairos_critic.md` in a fresh context with the spec and the paths it
references. If your harness cannot spawn one, say so and stop: a review in the
same conversation inherits the blind spots it is meant to find.

This is the one step with no measurement behind it. It costs a few thousand
tokens and the argument for it is reasoning, not data.

---

## Step 9 — validate the structure

```bash
openspec validate add-rate-limit
```

This checks the change is structurally valid for OpenSpec. It does **not** check
that the code will match it — that is step 10.

---

## Step 10 — the gate

```bash
kairos gate \
  --spec openspec/changes/add-rate-limit/specs/api/spec.md \
  --base main \
  --verify "python3 run_tests.py"
```

Exit `0` is READY. Anything else is not.

```text
✅ KAIROS GATE — READY
  spec:            spec.md
  completeness:    7/8 (threshold 6)
  acceptance:      3 criteria
  diff:            4 file(s), +67/-0 lines
  verification:    `python3 run_tests.py` -> exit 0 (0.02s)
  findings:        none
```

### What each verdict means in practice

**REPAIR — scope drift.** You touched a file the design did not name. Either
declare it or remove the change. On the test project this fired because a
`run_tests.py` helper was added and the design listed only three files.

**REPAIR — weakened assertion.** A test was made weaker inside a file that is new
to this branch. This is the case that made the incremental scan necessary: the
base diff sees only additions, so there is no "before" to compare. The gate now
also diffs `HEAD~1..HEAD`.

**BLOCKED — spec too weak.** Under 6 of the 8 measured sections. A weak spec makes
"the diff matches the spec" meaningless, so the gate refuses to give a verdict on
a document that could not constrain anything.

**BLOCKED — verification failed.** The `--verify` command exited non-zero. Without
`--verify`, the report says `verification: NOT RUN — so 'tests pass' is a claim`
rather than implying it passed.

### The rules that are off by default

Three scanner rules ship disabled because their measured precision on 370 real
merged pull requests was 0–17%: `guard_removal`, `phantom_stub`,
`silent_failure_empty_catch`. `weakened_assertion` is also off by default, at 0%
in a single observation — turn it on with `--enable-rule weakened_assertion` when
you are reviewing test changes specifically, which is what the test project did.

---

## Step 11 — archive

```bash
openspec archive add-rate-limit
```

Folds the delta into `openspec/specs/` and moves the change to `archive/`.

---

## In CI

[`examples/github-actions/kairos-gate.yml`](../examples/github-actions/kairos-gate.yml)
runs step 10 on every pull request. It needs `fetch-depth: 0`, because the gate
diffs against the base branch.

---

## What this cycle does not do

- It does not run your tests unless `--verify` is given.
- It compares words, not meaning: a test named after a criterion but asserting
  nothing passes the drift check.
- It cannot tell an intentional deletion from a fraudulent one.
- The fresh-context review is unmeasured.
- **Success rate is unmeasured.** The gate has 10 checks; none has been measured
  against real review outcomes. `docs/EVIDENCE.md` says so plainly. The only
  measured numbers in this repository are the scanner's precision on 370 PRs and
  the external SDD benchmark.

The honest way to get that number: run this cycle on 2–3 real repositories for a
few weeks and count how many REPAIR verdicts were real findings versus noise.
