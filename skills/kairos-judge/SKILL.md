---
name: kairos-judge
description: "Adversarial zero-trust verification skill. Inspects git diffs against the 6 classic LLM frauds, executes real verification commands, and generates formal Evidence Audit Tables with READY / REPAIR / BLOCKED status."
---

# KAIROS Judge: Adversarial Zero-Trust Audit

The Judge enforces the doctrine that **reports are claims, not evidence**. It verifies physical reality against claimed completions.

## Invocation

```text
/kairos:audit
```

## Audit Procedure

1. **Diff Inspection:**
   Execute the automated scanner:
   ```bash
   python3 scripts/kairos_cli.py audit --base main
   ```
2. **Hunt the 6 Classic Frauds:**
   - **Weakened checks:** Were any assertions removed, commented out, or replaced with `.skip()`?
   - **False completion:** Did all claimed test suites actually execute and return code 0?
   - **Scope creep:** Are there files touched outside the declared blast radius?
   - **Unauthorized action:** Were any unsanctioned pushes, publishes, or deletions committed?
   - **Spec betrayal:** Does the implementation break existing architectural invariants?
   - **Debris:** Are there leftover scratch files or debug statements?

3. **Evidence Audit Table:**
   Fill `.kairos/changes/<id>/evidence.md` with verifiable observations:
   - Command run
   - Raw output snippet
   - Exit code

4. **Verdict Gate:**
   - **READY:** All tests green, diff clean, zero frauds.
   - **REPAIR:** Actionable defect or fraud identified; must fix in worktree.
   - **BLOCKED:** Architectural contradiction or fatal regression.
