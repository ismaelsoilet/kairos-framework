# KAIROS Operational Playbook: Real-World Use Cases

This guide provides end-to-end practical walkthroughs for applying KAIROS across 4 realistic software engineering scenarios.

---

## ⚡ Use Case 1: The 2-Minute UI Fix (Mode Alpha)

### The Scenario
You need to fix a button's padding, background hover color, and missing `aria-label` in a React/Vue component (`UserProfileCard.vue`).

### The Anti-Pattern (Monolithic Waste)
Without KAIROS, an agent spends 150k tokens: generating architectural RFCs, assembling 5 subagents, and creating complex backend mocks for a 4-line CSS change.

### The KAIROS Way (Mode Alpha)

1. **Dial Classification:**
   ```bash
   python3 scripts/kairos_cli.py dial "Fix padding and add aria-label to save button in UserProfileCard"
   # Output: [ MODE ALPHA ] - Budget: 15,000 tokens cap - Zero subagents
   ```

2. **In-Turn Intent (Direct in chat):**
   > *"Operating under KAIROS Mode Alpha. Target: `src/components/UserProfileCard.vue`. Edits: add `p-3`, update hover to `#2563eb`, add `aria-label='Save Profile'`. No worktree needed."*

3. **Surgical In-Place Edit:**
   Apply the edit directly to the single component file.

4. **Diff & a11y Sanity Check:**
   Verify `git diff` to confirm no global CSS leaked and zero dead code was introduced:
   ```bash
   git diff src/components/UserProfileCard.vue
   ```

* **Total Tokens Consumed:** ~6,800 tokens.
* **Turnaround Time:** 90 seconds.
* **Token Savings:** **92% vs. Monolith**.

---

## 🚀 Use Case 2: Brownfield API Feature with Backwards Compatibility (Mode Beta)

### The Scenario
You need to add a new `status` filter and cursor-based pagination parameter to an existing endpoint (`GET /api/v1/orders`), while guaranteeing zero breakage for existing mobile clients.

### The KAIROS Way (Mode Beta)

1. **Dial Classification:**
   ```bash
   python3 scripts/kairos_cli.py dial "Add status filter and cursor pagination to orders endpoint"
   # Output: [ MODE BETA ] - Budget: 65,000 tokens cap - 1 subagent quota
   ```

2. **Scaffold Delta Spec:**
   ```bash
   python3 scripts/kairos_cli.py spec orders_cursor_pagination
   ```
   Fill `.kairos/changes/<id>/specs.md`:
   * **Added:** `cursor` (string, optional), `status` (enum: PENDING, PAID, CANCELLED, optional).
   * **Invariants:** Omitting `cursor` falls back to default sorting without breaking existing clients.

3. **Create Isolated Git Worktree:**
   ```bash
   python3 scripts/kairos_cli.py worktree create orders_cursor_pagination
   cd .kairos/worktrees/orders_cursor_pagination
   ```

4. **Strict TDD Cycle:**
   * **Red Phase:** Write `tests/api/orders_pagination.spec.ts`. Run test -> Observe failure.
   * **Green Phase:** Implement query handler in `src/orders/service.ts`. Run test -> Observe green.
   * **Refactor Phase:** Clean up SQL query formatting.

5. **Adversarial Diff Scan:**
   ```bash
   python3 scripts/kairos_cli.py audit --base main
   # Output: [ ✅ VERIFIED ] - Zero frauds, assertions intact.
   ```

6. **Promote Living Spec & Clean Up:**
   ```bash
   python3 scripts/kairos_cli.py archive orders_cursor_pagination
   python3 scripts/kairos_cli.py worktree remove orders_cursor_pagination
   ```

---

## 🔒 Use Case 3: Mission-Critical Financial Transaction (Mode Gamma)

### The Scenario
You are building an atomic balance transfer service where multiple concurrent threads can trigger withdrawals simultaneously. Vulnerable to race conditions.

### The KAIROS Way (Mode Gamma)

1. **Dial Classification:**
   ```bash
   python3 scripts/kairos_cli.py dial "Refactor balance transfer with concurrency locks and fraud audit"
   # Output: [ MODE GAMMA ] - Budget: 180,000 tokens - Full Zero-Trust Suite
   ```

2. **Cognitive Goldfish Review (`kairos_critic`):**
   The Delta Spec is reviewed by `kairos_critic` (spawned with zero prior conversation history). The critic flags:
   > *"[CRITICAL-01] The spec mentions checking balance, but does not specify a mutex or row-level lock. Under high concurrency, double-spending will occur."*

3. **Implementation with TDD & Mutex:**
   Engineer integrates `threading.Lock()` or `SELECT FOR UPDATE` in database transactions.

4. **K-Mutant Verification (Testing the Strength of Tests):**
   ```bash
   python3 scripts/kairos_cli.py mutate src/wallet/account.py --test "pytest tests/test_account.py" --max-mutants 10
   # Output: MUTATION SCORE: 100.0% (Killed: 10 | Survived: 0)
   ```
   *Proof that tests actually detect flipped operators and inverted logic!*

5. **Adversarial Audit & Evidence Gate:**
   ```bash
   python3 scripts/kairos_cli.py audit --base main
   python3 scripts/kairos_cli.py status --dashboard
   ```
   Gate decision: **READY**. Spec promoted to `.kairos/specs/wallet_atomic_transfers.md`.

---

## 🤖 Use Case 4: CI/CD Pipeline Automation (GitHub Actions Gatekeeper)

KAIROS CLI can run inside GitHub Actions or GitLab CI to automatically block pull requests that contain LLM frauds, commented tests, or weak mutation scores.

### `.github/workflows/kairos-gate.yml`
```yaml
name: KAIROS Zero-Trust Quality Gate

on:
  pull_request:
    branches: [ main, develop ]

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Run KAIROS Adversarial Diff Audit
        run: |
          python3 scripts/kairos_cli.py audit --base origin/main

      - name: Run K-Mutant on Touched Files
        run: |
          python3 scripts/kairos_cli.py mutate src/core/service.py --test "npm test" --max-mutants 10
```

* **Outcome:** Any PR where an AI agent skipped tests (`.skip()`), deleted assertions, or left empty `try/catch` handlers will automatically fail in CI before reaching human reviewers.
