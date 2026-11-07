# Proposal: KAIROS Engine Expansion (Mutation Testing, Visual Dashboard & Rollback)
* **ID:** 20261107_185250_mutation_dashboard_rollback
* **Created:** 2026-11-07 18:52:50
* **Mode:** GAMMA
* **Author:** ismaelsoilet

## 1. Intent & Context
Elevate KAIROS from a diff-regex scanner into an industrial-grade verification engine by adding:
1. **K-Mutant (Mutation Testing Engine):** Mathematically proves whether test suites actually catch bugs or are tautological mocks.
2. **Visual Dashboard (`kairos status --dashboard`):** ANSI-based progress bars for stages and token gauge.
3. **Automated Rollback (`kairos rollback`):** Safe, one-command restoration of worktree state upon REPAIR or BLOCKED verdicts.

## 2. In Scope
- Add `cmd_mutate` to `kairos_cli.py`: Injects syntactic mutations into a target file, runs a provided test command, and reports mutation kill score.
- Add `--dashboard` flag to `cmd_status` with ANSI stage progress bar and token gauge.
- Add `cmd_rollback` to `kairos_cli.py`: Discards uncommitted or bad work in worktree.
- Add unit tests for these new features in `tests/test_cli_features.py`.

## 3. Explicitly Out of Scope (Non-Goals)
- No external heavy dependencies (NO third-party mutation frameworks like cosmic-ray or mutmut; pure Python 3 native AST/regex mutations).
- No changes to existing dial classification heuristics.

## 4. Key Risks & Operational Constraints
- Mutation testing must always restore the original source file, even if the test run raises an unexpected exception (using `try...finally`).
- Terminal dashboard must render cleanly on both standard terminals and CI environments without color code corruption.
