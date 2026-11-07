---
name: kairos-build
description: "Executes implementation with absolute workspace isolation via git worktrees, strict Test-Driven Development (Red-Green-Refactor), and reproducible debugging."
---

# KAIROS Build: Isolated Execution & Strict TDD

The Build skill implements approved specifications while strictly protecting the main branch and preventing regressions.

## Invocation

```text
/kairos:build
```

## Protocol Steps

### 1. Workspace Isolation
In Mode Beta and Gamma, verify worktree isolation:
```bash
python3 scripts/kairos_cli.py worktree create <task_name>
```
If already inside an isolated worktree or branch, skip creation.

### 2. The Strict TDD Cycle
For each task item in `tasks.md`:

```
+-------------------------------------------------------------+
| 1. RED: Write the failing test. Run it. Observe failure.   |
| 2. GREEN: Write minimal code. Run test. Observe pass.       |
| 3. REFACTOR: Clean up code while keeping test green.        |
+-------------------------------------------------------------+
```

* **Violation Rule:** If code is written before observing the test fail, delete the code immediately and start fresh from the test.

### 3. Systematic Debugging
If a test or build fails unexpectedly:
1. Do not apply speculative "maybe this works" patches.
2. Isolate the failing test to a minimal reproduction command.
3. Inspect call stacks, parameters, and logs to identify root cause.
4. Apply the targeted fix and verify that all regression tests pass.
