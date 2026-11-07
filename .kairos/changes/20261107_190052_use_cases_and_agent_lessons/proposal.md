# Proposal: KAIROS Real-World Use Cases, Agent Lessons & Skills Enhancement
* **ID:** 20261107_190052_use_cases_and_agent_lessons
* **Created:** 2026-11-07 19:00:52
* **Mode:** BETA
* **Author:** ismaelsoilet

## 1. Intent & Context
While KAIROS has a powerful core engine, developers and autonomous agents need:
1. **Concrete Real-World Use Cases (`docs/USE_CASES.md` & `docs/USE_CASES.pt-br.md`):** Step-by-step walkthroughs showing how to apply KAIROS to real engineering problems (Hotfixes in Mode Alpha, Brownfield APIs in Mode Beta, Financial Security in Mode Gamma, and CI/CD PR Gates).
2. **Agent Lessons & Cognitive Playbook (`docs/AGENT_LESSONS.md`):** Concrete lessons extracted from real LLM failure modes (tautological tests, mock decay, sycophantic approval, token waste) and instructions on how human engineers can pair effectively with KAIROS.
3. **Upgraded Skills & Agents:** Incorporate the new `mutate`, `rollback`, and `--dashboard` capabilities into `skills/` and sharpen agent instructions in `agents/`.

## 2. In Scope
- Create `docs/USE_CASES.md` and `docs/USE_CASES.pt-br.md`.
- Create `docs/AGENT_LESSONS.md`.
- Update `skills/kairos-judge/SKILL.md` (add K-Mutant guidelines).
- Update `skills/kairos-orchestrator/SKILL.md` (add dashboard and rollback orchestration).
- Enhance subagent personas in `agents/`.

## 3. Explicitly Out of Scope (Non-Goals)
- No breaking changes to existing CLI commands or state format.

## 4. Key Risks & Operational Constraints
- Documentation must remain deeply technical and actionable, avoiding generic filler prose.
