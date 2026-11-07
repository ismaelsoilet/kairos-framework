# Specification & Behavioral Contracts: Engine Expansion
* **Change ID:** 20261107_185250_mutation_dashboard_rollback

## 1. Added Behaviors (NEW)

### REQ-01: Mutation Testing Command (`kairos mutate`)
* **Given:** A target file `F` and a test command `CMD`.
* **When:** The user executes `python3 scripts/kairos_cli.py mutate <target_file> --test "<CMD>"`.
* **Then:** KAIROS creates synthetic mutations in `F` (e.g. `==` to `!=`, `>=` to `<`, `+` to `-`, `True` to `False`), runs `CMD` for each mutant.
* **Criterion:** If `CMD` fails (exit != 0), the mutant is **KILLED** (Good). If `CMD` succeeds (exit == 0), the mutant **SURVIVED** (Weak test).
* **Safety Invariant:** The original file `F` is 100% restored upon completion.

### REQ-02: Visual Dashboard (`kairos status --dashboard`)
* **Given:** Current state in `.kairos/state.json`.
* **When:** `python3 scripts/kairos_cli.py status --dashboard` is called.
* **Then:** Outputs an ASCII/ANSI progress bar representing the current stage among the 7 official stages and a visual token consumption gauge.

### REQ-03: Safe Worktree Rollback (`kairos rollback`)
* **Given:** Uncommitted or broken changes in active worktree or working copy.
* **When:** `python3 scripts/kairos_cli.py rollback` is called.
* **Then:** Runs `git reset --hard HEAD` and `git clean -fd`, restoring state to clean commit and setting `current_stage` to `ROLLED_BACK`.

## 2. Invariants (Things that MUST NEVER break)
- [ ] Source files must NEVER remain mutated after `kairos mutate` finishes or crashes.
- [ ] Zero external dependencies added to `kairos_cli.py`.
