---
name: kairos-dial
description: "Calibrates task complexity and enforces the KAIROS Elastic Dial. Classifies demands into Mode Alpha (Lite/UI), Mode Beta (Standard), or Mode Gamma (Critical), establishing token budgets and workflow constraints."
---

# KAIROS Elastic Dial: Complexity & Token Budgeting

The Elastic Dial prevents the two catastrophic failure modes of agentic development:
1. **Under-engineering critical systems** (breaking production due to lack of tests and specs).
2. **Over-engineering trivial updates** (burning 200k tokens and 20 minutes to fix a button style).

## Invocation

```text
/kairos:dial <task description>
```

## Mode Matrix & Constraints

| Metric | Mode Alpha (Lite / UI) | Mode Beta (Standard) | Mode Gamma (Critical) |
| :--- | :--- | :--- | :--- |
| **Typical Target** | UI fixes, CSS tweaks, typos, single component adjustments (<30 LOC). | Single feature, new endpoint, DTO change, bugfix. | Auth, security, billing, transactions, migrations, breaking contracts. |
| **Token Target** | **5k - 15k tokens** | **30k - 65k tokens** | **120k - 200k tokens** |
| **Subagents Allowed**| **0 (Zero)** | **1 max** | **Up to 3** (`kairos_critic`, `kairos_worker`, `kairos_auditor`) |
| **Workspace** | Direct in-place edit | Git Worktree / Isolated Branch | Git Worktree mandatory |
| **Specification** | In-turn chat block | Delta Spec in `.kairos/changes/` | Full Delta Spec + Goldfish Swarm review |
| **Verification** | Visual & diff sanity | TDD suite + automated diff audit | TDD suite + zero-trust adversarial report |

## Classification Algorithm

Execute the CLI helper or evaluate the following risk rules:
```bash
python3 scripts/kairos_cli.py dial "<task description>"
```

* **If task contains UI, CSS, button, copy, typo, layout:** -> Default to **ALPHA**.
* **If task contains auth, security, crypto, database, migration, payment, core:** -> Default to **GAMMA**.
* **All other feature work and bug fixes:** -> Default to **BETA**.
