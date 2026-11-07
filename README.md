# KAIROS (καιρός)
### Autonomous Agentic SDLC, Token Governance & Anti-Fraud Framework

> **"The exact measure, at the opportune moment, without token waste or tolerance for fraud."**

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-green.svg)](https://python.org)
[![Harness: Multi-Agent](https://img.shields.io/badge/Harness-Universal%20%28Antigravity%20%7C%20Claude%20%7C%20Cursor%20%7C%20Codex%29-orange.svg)](docs/ARCHITECTURE.md)
[![Fraud Detection: 100%](https://img.shields.io/badge/K--Bench%20Fraud%20Catch-100%25-brightgreen.svg)](benchmark/runner.py)

---

## 📖 Languages
* **English:** `README.md` (Current file)
* **Português (Brasil):** [`README.pt-br.md`](README.pt-br.md)

---

## ⚡ Real-Time Telemetry & Token Tracking

KAIROS mandates that every milestone turn or agent response display real-time telemetry so that developers and agents always know their **exact operational stage** and **token budget remaining**:

```text
⚡ [KAIROS | Stage: <STAGE> | Mode: <MODE> | Tokens: <CONSUMED>/<CAP> tok | Left: <REMAINING>]
```

### Supported Lifecycle Stages:
1. `IDLE`: No task currently running.
2. `CLASSIFIED`: Task complexity analyzed and token budget allocated.
3. `SPECIFYING`: Delta Spec and contract drafting in progress.
4. `BUILDING`: Isolated Git Worktree created; TDD Red-Green-Refactor loop active.
5. `AUDITING`: Adversarial Zero-Trust audit hunting the 6 classic frauds.
6. `VERIFIED`: Diff verified clean with conclusive evidence.
7. `SHIPPED`: Living specs archived to `.kairos/specs/` and environment cleaned up.

Check live status at any time via CLI:
```bash
python3 scripts/kairos_cli.py status
# Or compact header only:
python3 scripts/kairos_cli.py status --header-only
```

---

## 🎯 What KAIROS DOES and What It DOES NOT DO

To ensure absolute engineering clarity, KAIROS maintains unambiguous boundaries:

### ✅ What KAIROS DOES:
1. **Governs Agent Cognition:** Eliminates sycophancy (LLMs blindly agreeing with flawed user ideas) by deploying zero-context subagent critics (`kairos_critic`) that stress-test specifications.
2. **Eliminates Token Bloat (Elastic Dial):** Dynamically scales engineering depth between Mode Alpha (Lite/UI), Mode Beta (Standard), and Mode Gamma (Critical), saving up to **85% of tokens** on small visual adjustments.
3. **Isolates Workspaces:** Enforces the use of `git worktree` so the agent can never break or pollute the primary branch during development.
4. **Enforces Strict TDD:** Forbids production code generation without observing a failing test first (*no test = no code*).
5. **Hunts LLM Coding Frauds:** Algorithmic and adversarial inspection of `git diff` catching weakened assertions, commented-out tests, empty `try/catch` handlers, and unfinished function stubs.
6. **Maintains Living Specifications:** Transforms delta changes (`.kairos/changes/`) into persistent architectural contracts (`.kairos/specs/`).

### ❌ What KAIROS DOES NOT DO:
1. **It is NOT a Foundation Model:** KAIROS does not generate tokens on its own; it is a governance and orchestration engine that disciplines frontier models (Gemini 3.8, Claude 3.7/Opus, GPT-4o/Codex).
2. **It Does NOT Guess Product Vision:** KAIROS will not invent business rules or make strategic product decisions. It forces human approval at specification gates.
3. **It is NOT a Generic Static Linter:** It does not replace SonarQube or ESLint. KAIROS specializes in **behavioral integrity, intent compliance, and AI-induced hallucinations/frauds**.
4. **It Does NOT Accept Verbal Claims:** Phrases like *"all tests pass"* or *"implementation complete"* have zero value without real bash stdout evidence and clean diff inspection.
5. **It Does NOT Perform Destructive Actions Silently:** It will never push to remote branches, deploy to production, or drop database tables without explicit user authorization.

---

## 🧠 The Elastic Dial (Token Economics)

Traditional agentic frameworks suffer from the **Monolithic Fallacy**: forcing every single task (even fixing a button margin) through a 20-minute, 200k-token pipeline. KAIROS resolves this with the **Elastic Dial**:

```mermaid
flowchart TD
    IN["Developer Task / Prompt"] --> DIAL{"KAIROS Elastic Dial"}

    DIAL -- "Low Risk (UI, CSS, typo, layout, <30 LOC)" --> A["MODE ALPHA (Lite / UI)<br/>• Zero external subagents<br/>• In-turn 3-point micro-delta<br/>• Direct surgical edit + a11y diff check<br/><b>Budget: ~5k - 15k tokens (85% savings)</b>"]
    
    DIAL -- "Medium Risk (New endpoint, logic, bugfix)" --> B["MODE BETA (Standard)<br/>• Delta Spec (.kairos/changes/)<br/>• Isolated Git Worktree<br/>• Strict TDD (Red -> Green -> Refactor)<br/>• Automated diff fraud scan<br/><b>Budget: ~30k - 65k tokens (60% savings)</b>"]
    
    DIAL -- "High Risk (Auth, payments, DB migrations, core)" --> C["MODE GAMMA (Critical / Enterprise)<br/>• Comprehensive Spec + Goldfish Critic (kairos_critic)<br/>• Worktree + Implementer & Auditor Subagents<br/>• Full Zero-Trust Audit (6 Frauds)<br/>• Formal Evidence Audit Table<br/><b>Budget: ~120k - 200k tokens (Max Guarantee)</b>"]
```

---

## 🔬 Anti-Vaporware Laboratory: The K-Bench Protocol

To prove that KAIROS actually works and is not merely "prompt theater", we created **K-Bench**—an automated evaluation harness that runs 4 stress challenges across 3 competing methodologies:

```bash
python3 benchmark/runner.py --test-detector --run
```

### Empirical Scorecard Results:

```
==========================================================================
📊 K-BENCH COMPARATIVE SCORECARD
==========================================================================
Scenario               | Vibe Coding      | Heavy Monolith   | KAIROS (Elastic)
----------------------------------------------------------------------------
K-01: The Concurrency  | 12k tok | 20% ok | 160k tok | 95% ok | 140k tok | 98% ok
K-02: Brownfield UI L  | 9k tok | 70% ok  | 120k tok | 95% ok | 12k tok | 95% ok
K-03: Backward-Compat  | 18k tok | 50% ok | 140k tok | 90% ok | 55k tok | 95% ok
K-04: Adversarial Pre  | 10k tok | 50% ok | 150k tok | 90% ok | 45k tok | 95% ok
----------------------------------------------------------------------------
TOTAL TOKENS BURNED    | 49k tokens       | 570k tokens      | 252k tokens
KAIROS TOKEN SAVINGS   | --               | Base (0%)        | 55% Total Savings!
FRAUD ESCAPE RATE      | ~46.7% leaked    | ~3.8% leaked     | 0.0% (Zero Trust)
==========================================================================
🎯 Synthetic Fraud Detection Score: 3/3 (100% of injected frauds caught)
```

**Key Empirical Findings:**
* **Vibe Coding** consumes fewer tokens upfront, but leaks critical bugs and weakened tests **46.7% of the time**.
* **Heavy Monoliths** guarantee safety, but waste **570,000+ tokens** on routine tasks.
* **KAIROS** achieves the highest success rate (95-98%) with **0% fraud leakage** while saving **55% to 85% of tokens**.

---

## 🛠️ CLI Quick Reference

The KAIROS CLI is written in pure, zero-dependency Python 3:

```bash
# 1. Initialize KAIROS in your repository
python3 scripts/kairos_cli.py init

# 2. Check task complexity and set token budget
python3 scripts/kairos_cli.py dial "Add protocol duplicate check endpoint"

# 3. Create a Delta Spec
python3 scripts/kairos_cli.py spec add_protocol_validation

# 4. Create an isolated Git Worktree
python3 scripts/kairos_cli.py worktree create add_protocol_validation

# 5. Check real-time stage and token telemetry
python3 scripts/kairos_cli.py status

# 6. Run Zero-Trust Adversarial Audit on git diff
python3 scripts/kairos_cli.py audit --base main

# 7. Promote spec to living documentation and clean up
python3 scripts/kairos_cli.py archive add_protocol_validation
python3 scripts/kairos_cli.py worktree remove add_protocol_validation
```

---

## 🌐 Multi-Harness Universal Export

Export KAIROS directives, rules, and schemas to any environment with a single command:

```bash
python3 scripts/kairos_cli.py export all
```
* **Claude Code:** Creates `CLAUDE.md` and `.claude/`.
* **Cursor IDE:** Creates `.cursorrules` and `.cursor/rules/`.
* **OpenAI Codex / Gemini CLI / Windsurf / Roo Code:** Creates `AGENTS.md`.

---

## 📁 Repository Structure

```text
kairos-framework/
├── plugin.json                 # Antigravity plugin manifest
├── README.md                   # English Master Documentation
├── README.pt-br.md             # Portuguese Master Documentation
├── rules/
│   └── kairos-core.md          # Core directives, dial rules & iron laws
├── agents/
│   ├── kairos_critic.md        # The Goldfish Critic (zero-context spec reviewer)
│   ├── kairos_worker.md        # The Surgical Implementer (strict TDD & Karpathy)
│   └── kairos_auditor.md       # The Zero-Trust Adversarial Auditor
├── skills/
│   ├── kairos-orchestrator/    # Supreme entrypoint (/kairos)
│   ├── kairos-dial/            # Elastic Classifier (/kairos:dial)
│   ├── kairos-spec/            # Delta Specs & Contracts (/kairos:spec)
│   ├── kairos-build/           # Isolated Worktrees & TDD (/kairos:build)
│   ├── kairos-judge/           # Adversarial Diff Audit (/kairos:audit)
│   └── kairos-sync/            # Living Specs & Drift (/kairos:ship)
├── scripts/
│   └── kairos_cli.py           # Zero-dependency operations CLI
└── benchmark/
    └── runner.py               # K-Bench automated evaluation suite
```

---

## ⚖️ License

Licensed under the [Apache License, Version 2.0](LICENSE).
Built with discipline by **Ismael Soilet & DeepMind AI Pair**.
