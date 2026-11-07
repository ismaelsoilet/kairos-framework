# Specification & Behavioral Contracts: Use Cases & Agent Lessons
* **Change ID:** 20261107_190052_use_cases_and_agent_lessons

## 1. Added Behaviors (NEW)

### REQ-01: Real-World Use Cases Playbook
* **Deliverable:** `docs/USE_CASES.md` (English) and `docs/USE_CASES.pt-br.md` (Português).
* **Must Cover 4 Distinct Scenarios:**
  1. *Scenario 1: The 2-Minute UI Hotfix (Mode Alpha)*: Step-by-step token-frugal surgical edit.
  2. *Scenario 2: Brownfield API Feature with Backwards Compatibility (Mode Beta)*: Delta Spec + Worktree + TDD.
  3. *Scenario 3: Mission-Critical Financial Transaction (Mode Gamma)*: Full Goldfish Swarm + Mutex implementation + K-Mutant testing + Adversarial Audit.
  4. *Scenario 4: CI/CD Pipeline Automation (GitHub Actions / GitLab CI)*: Running `kairos audit` and `kairos mutate` on Pull Requests.

### REQ-02: Agent Lessons & Cognitive Playbook
* **Deliverable:** `docs/AGENT_LESSONS.md`.
* **Must Cover:**
  - 10 Iron Heuristics learned from agent failures (Sycophancy traps, tautological mocks, regex vs AST diff analysis, etc.).
  - Protocol for pairing human engineers with KAIROS agents.
  - Multi-agent delegation patterns.

### REQ-03: Skills & Agent Personas Upgrades
* **Update `skills/kairos-judge/SKILL.md`:** Incorporate `kairos mutate` into the verification checklist.
* **Update `skills/kairos-orchestrator/SKILL.md`:** Incorporate `status --dashboard` and `rollback` into lifecycle stages.
* **Update `agents/`:** Enrich `kairos_critic.md`, `kairos_worker.md`, and `kairos_auditor.md` with explicit anti-patterns.
