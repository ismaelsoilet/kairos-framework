---
name: kairos-judge
description: "Adversarial zero-trust verification skill. Inspects git diffs against the 6 classic LLM frauds, executes K-Mutant mutation tests, and generates formal Evidence Audit Tables with READY / REPAIR / BLOCKED status."
---

# KAIROS Judge: Adversarial Zero-Trust Audit & Mutation Verification

The Judge enforces the doctrine that **reports are claims, not evidence**. It verifies physical reality against claimed completions.

## Invocation

```text
/kairos:audit
```

## Audit Procedure

### 1. Diff Inspection (Hunting the 6 Classic Frauds)
Execute the automated scanner:
```bash
python3 scripts/kairos_cli.py audit --base main
```
* **Weakened checks:** Were any assertions removed, commented out, or replaced with `.skip()`?
* **False completion:** Did all claimed test suites actually execute and return code 0?
* **Scope creep:** Are there files touched outside the declared blast radius?
* **Unauthorized action:** Were any unsanctioned pushes, publishes, or deletions committed?
* **Spec betrayal:** Does the implementation break existing architectural invariants?
* **Debris:** Are there leftover scratch files or debug statements?

### 2. Mutation Strength Verification (K-Mutant Engine)
In Mode Beta and Gamma, verify that the tests are not tautological mocks:
```bash
python3 scripts/kairos_cli.py mutate <target_file> --test "<test_command>" --max-mutants 10
```
* If mutants survive, the test suite is weak. The developer must add assertions before approval.

### 3. Visual Mission Control Status
Verify the overall pipeline state:
```bash
python3 scripts/kairos_cli.py status --dashboard
```

### 4. Evidence Audit Table & Gate Decision
Fill `.kairos/changes/<id>/evidence.md` with verifiable observations:
- Command run
- Raw output snippet
- Exit code
- Mutation kill score

**Gate Status:**
* **READY:** All tests green, diff clean, mutation score > 80%, zero frauds detected.
* **REPAIR:** Actionable defect, mutation survival, or fraud identified; must fix in worktree or run `kairos rollback`.
* **BLOCKED:** Architectural contradiction or fatal regression.
