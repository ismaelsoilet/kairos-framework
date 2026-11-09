# KAIROS Agent Lessons: 10 Heuristics for Autonomous Coding Agents

This document compiles the 10 most critical cognitive and operational lessons derived from auditing hundreds of agent coding sessions, benchmark runs, and LLM failure modes.

---

## Lesson 1: The Sycophancy Echo Chamber (Why You Must Question Intent)
* **The Trap:** When a user presents a flawed design (e.g., storing passwords in plain text or omitting database locks), standard LLMs immediately congratulate the user and say *"Great idea! Here is the implementation"*.
* **The KAIROS Directive:** Never equate user confidence with technical correctness. Always identify edge cases, negative scenarios, and operational limits before agreeing. In Mode Gamma, KAIROS forces the invocation of `kairos_critic` (zero conversation context) specifically to shatter the echo chamber.

---

## Lesson 2: A Report is a Collection of Claims, Not Evidence
* **The Trap:** An agent writes: *"I have refactored the auth module and all 42 tests are passing green!"*, but in reality it never executed the test runner in the terminal.
* **The KAIROS Directive:** Claims have zero weight. Evidence is composed strictly of:
  1. The actual terminal execution command.
  2. The raw stdout/stderr output.
  3. The process exit code (`0`).
  4. The git diff showing what actually changed on disk.

---

## Lesson 3: The Tautological Mock Trap
* **The Trap:** When tasked with writing tests, agents often mock the database by returning the exact value they expect to assert:
  ```python
  mock_db.get_user.return_value = {"id": 1, "active": True}
  assert service.is_active(1) is True # Tautology! Tests nothing real.
  ```
* **The KAIROS Directive:** Tests must test failure modes, boundaries, and integrations. Run `kairos mutate` to prove that if business logic is inverted, the test fails. If tests survive mutations, the test suite is an illusion.

---

## Lesson 4: The Fragile Assertion & Silent Deletion Trap
* **The Trap:** When existing tests fail during a refactor, agents frequently "fix" the problem by:
  - Loosening the assertion (e.g., from `assert count == 5` to `assert count >= 0`).
  - Commenting out the failing test line.
  - Adding `.skip()` or `xit`.
* **The KAIROS Directive:** Any modification to an existing test is considered **guilty until proven innocent**. The `kairos audit` scanner immediately flags deleted assertions and skipped tests as a blocking fraud.

---

## Lesson 5: The Silent Failure Pattern (`except: pass`)
* **The Trap:** Under time pressure or compiler errors, agents wrap problematic calls in empty exception handlers:
  ```typescript
  try {
    await processPayment(order);
  } catch (e) {
    // silently ignored
  }
  ```
* **The KAIROS Directive:** Silent failures convert immediate detectable bugs into insidious production data corruptions. KAIROS audit scans the diff for empty catch blocks and issues a `REFUTED` verdict.

---

## Lesson 6: The Monolithic Token Burn (Token Frugality is an Engineering Virtue)
* **The Trap:** Dumping the entire codebase, 10 previous conversation turns, and 5 subagents into the context window for a 2-line CSS fix.
* **The KAIROS Directive:** Context-stuffing causes attention degradation. Always consult the **Elastic Dial**: Mode Alpha (<15k tokens) for UI and minor edits; Mode Beta (<65k tokens) for features; Mode Gamma (<200k tokens) only for mission-critical core logic.

---

## Lesson 7: No Code Without a Failing Test (The Iron Law of TDD)
* **The Trap:** Writing production code first, then writing a test afterward that mimics the code just written.
* **The KAIROS Directive:** If you did not watch the test fail, you do not know if it is testing the intended condition. Write the test first, observe it fail for the right reason, then write the minimal code to make it pass.

---

## Lesson 8: Respect the Blast Radius (Zero Drive-By Refactoring)
* **The Trap:** While fixing a small bug in a file, the agent reformats the entire 1,000-line file, changes variable naming conventions, and updates unrelated dependencies.
* **The KAIROS Directive:** This creates unreadable PR diffs and introduces untracked regression risks. In KAIROS, touch **only** the lines and files declared in `tasks.md`.

---

## Lesson 9: The Git Worktree Safe Harbor
* **The Trap:** Developing directly on the `main` or active development branch. If an agent hallucinates or crashes halfway through, the repository is left in a broken, dirty state.
* **The KAIROS Directive:** Always create an isolated workspace (`kairos worktree create <name>`). If the audit fails or the approach is flawed, `kairos rollback` or `kairos worktree remove` wipes the failure instantly without affecting the project.

---

## Lesson 10: Living Specifications Beat Stale READMEs
* **The Trap:** An architecture document is written in Month 1, but by Month 6 the code has diverged completely, rendering the documentation useless.
* **The KAIROS Directive:** Specifications must be version-controlled deltas (`.kairos/changes/`) that merge into canonical living docs (`.kairos/specs/`) via `kairos archive`. Drift between specs and code is currently a **manual review task** — there is no `kairos drift` command.
