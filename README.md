# KAIROS (καιρός)

### A process-governance layer for coding agents — specs, TDD, mutation testing, and diff auditing

> **"The exact measure, at the opportune moment."**
>
> On the name: *kairos* is the Greek word for the right moment, as opposed to *chronos*, mere elapsed time. The project earned the name badly for its first year. See below.

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-green.svg)](https://python.org)
[![Version: 1.2.0](https://img.shields.io/badge/Version-1.2.0-blueviolet.svg)](plugin.json)

---

> ## ⚠️ Retraction notice (2026-11-08)
>
> Versions up to v1.1.0 published token-savings percentages, success rates and "empirical benchmark" results on this page. **Those numbers were not measured.** They were constants written into the benchmark scripts and printed as if they were observations.
>
> **All of them are withdrawn.** Read [`RETRACTION.md`](RETRACTION.md) for the full list, the mechanism behind each one, and what was actually true.
>
> This README no longer contains a quantitative performance claim, because none currently meets the evidence bar this project sets for others. Claims may return when they carry a reproducible artifact — see [`CLAIMS.md`](CLAIMS.md).

**Languages:** English (this file) · [Português (Brasil)](README.pt-br.md)

---

## What KAIROS is

KAIROS is a set of conventions plus a zero-dependency Python CLI that impose a disciplined process on an AI coding agent:

- classify the task's risk before doing work
- write a delta spec before writing code
- implement inside an isolated `git worktree`
- write the failing test first
- mutate the implementation and confirm the tests catch it
- scan the resulting `git diff` for signs that the agent cheated
- archive the spec and record the lesson

It does not generate code. It does not call a model. It has no opinion about which model you use. It is the part that refuses to take the agent's word for it.

Everything below is either implemented in `scripts/kairos_cli.py` or marked as not implemented. That distinction is the point of v1.2.

---

## Capability status

Honest tiering. If a capability is in the third column, do not plan around it.

### Implemented and covered by tests

| Capability | Command | Test evidence |
| :--- | :--- | :--- |
| Project state, atomic writes, reentrant lock | `init`, `status` | `atomic_state_save`, `state_file_locking_context_manager` |
| Risk classification (keyword-based) | `dial` | `dial_security_and_financial_prioritization` |
| Delta spec scaffolding (5 files) | `spec` | `spec_name_sanitization_rejects_path_traversal` |
| Diff fraud scanning | `audit` | 15 positive/negative scanner tests |
| Manifest reconnaissance | `scout` | `scout_detects_cutoff_risk_packages`, `scout_cli_execution` |
| Skill/agent discovery | `registry` | `registry_discovers_agents_and_skills` |
| In-repo lessons | `lesson add/list` | `lesson_add_and_list` |

### Implemented, untested

`worktree create/remove/list`, `archive`, `export`, `rollback`, the `mutate` engine end-to-end (only its operator table is asserted), and `status --dashboard` rendering. Listed here deliberately: a command exiting 0 is not evidence that it works.

### Documented, not implemented

- **`kairos drift`** — referenced by `skills/kairos-sync/SKILL.md` and `docs/AGENT_LESSONS.md`. The subcommand does not exist. Removed from the docs in v1.2 pending implementation or removal.
- **Blast-radius enforcement** — `docs/ARCHITECTURE.md` claimed the scanner compares touched files against paths declared in `tasks.md`. It does not. Scope creep is a review responsibility, not a scanner feature, until implemented.
- **`invoke_subagent(...)`** — appears as code in two skills. It is a harness primitive, not provided by this repository. Skills now say so explicitly.

---

## The five iron laws

From [`rules/kairos-core.md`](rules/kairos-core.md):

1. **No production code without a failing test.** If you did not watch it fail, you do not know what it tests.
2. **No guesswork in debugging.** Reproduce the defect in a minimal test before touching production code.
3. **Ground truth is `git diff`.** Claims are not evidence. Command output and diff inspection are.
4. **Hunt the six classic frauds** — weakened checks, false completion, scope creep, unauthorized action, spec betrayal, debris.
5. **Living specifications.** Finished work archives its spec into `.kairos/specs/`.

Law 3 is the one this project violated most thoroughly, and the reason for the retraction above.

---

## The Elastic Dial

Three process depths, chosen by the classifier in `dial`:

| Mode | Intended for | Pipeline | Subagents | Budget target |
| :--- | :--- | :--- | :--- | :--- |
| **Alpha** | UI, copy, layout, CSS, small edits | in-turn micro-delta, surgical edit, diff sanity check | 0 | small |
| **Beta** | new endpoint, logic change, bugfix | manifest recon → delta spec → worktree → strict TDD → diff scan | 1 | medium |
| **Gamma** | auth, payments, migrations, core logic | recon → spec + zero-context critic → worktree → TDD → mutation testing → adversarial audit | up to 3 | large |

**Known limitation, stated plainly:** classification is keyword matching over the task description (`ALPHA_KEYWORDS` / `GAMMA_KEYWORDS` in `kairos_cli.py`). It has no knowledge of which files you will touch, how large the diff is, or whether the area is covered by tests. Consequences:

- A CSS fix that mentions "balance" classifies as **Gamma**.
- `--force-beta` does not override a Gamma keyword (fix in progress).
- The budget figures are planning targets, not measurements. KAIROS does not measure your token consumption. See "Telemetry".

A risk router based on objective signals — changed paths, diff size, test coverage of the area, incident history — is the honest version of this idea and is not built yet. See [`docs/OPPORTUNITIES.md`](docs/OPPORTUNITIES.md).

---

## The four personas

| Agent | Role | What it actually does |
| :--- | :--- | :--- |
| `kairos_scout` | Technology Scout | Reads dependency manifests and flags packages with a history of breaking API changes. Nothing more. |
| `kairos_critic` | Goldfish Critic | Reviews a spec with no conversation context, so it cannot be talked into agreeing. |
| `kairos_worker` | Surgical Implementer | TDD inside a worktree; touches only declared files. |
| `kairos_auditor` | Diff Auditor | Re-runs commands, inspects the diff, reports evidence. Its verdict is only as good as the scanner — read the limitations below before trusting it. |

---

## What the scanner actually catches

`scan_diff_text()` runs regular expressions over added lines of a `git diff`. It reliably catches **literal** forms of:

- skipped, focused or commented-out tests (`test.skip`, `xit`, `@pytest.mark.skip`, `// assert ...`)
- empty or swallowed exception handlers (`except: pass`, `catch (e) {}`)
- stubs returning trivial constants (`def f(): pass`, `return null;`)
- tautological assertions (`assert True`, `assert 1 == 1`, `expect(true).toBeTruthy()`)
- net assertion or test-function deletion
- deprecated model identifiers in code

It **does not** catch, as of v1.2:

- an assertion weakened in place (`assert x == 'valid'` → `assert x is not None`)
- a handler that logs the error and then returns success
- a mock substituted for the unit under test
- a validation function that unconditionally returns `True`
- a removed guard clause

An independent probe of eight fraud patterns detected three. The corpus under `tests/fixtures/fraud_corpus/` exists to make that number measurable and to raise it; the current measured recall and precision are in [`CLAIMS.md`](CLAIMS.md) — whatever the corpus run reports, not a target restated as a result.

**The scanner no longer excludes its own source file from auditing.** Through v1.1.0 it did (`if current_file.endswith("kairos_cli.py"): continue`), which meant the tool could not audit the tool. That exclusion is gone.

---

## Telemetry: what it measures and what it does not

The status line looks like this:

```text
⚡ [KAIROS | Stage: BUILDING | Mode: BETA | Budget: 65,000 | Spent: UNMEASURED]
```

`Stage` and `Mode` come from `.kairos/state.json`. `Budget` is a planning target.

`Spent` is **`UNMEASURED`** until you import real usage data with `kairos token import --usage <log.jsonl>`, which parses actual input/output/cache token counts and cost from a harness log and records the source file hash alongside them. Through v1.1.0 the field was filled by `kairos token add <n>` — the agent incrementing its own counter, which is the exact failure mode this project claims to detect. That command is removed.

If nothing is measured, the status says so. It does not print zero and let you infer that zero tokens were spent.

---

## Install and first run

Requires Python 3.10+. No dependencies.

```bash
git clone https://github.com/ismaelsoilet/kairos-framework
cd your-project
python3 /path/to/kairos-framework/scripts/kairos_cli.py init
python3 /path/to/kairos-framework/scripts/kairos_cli.py dial "add retry to the payment webhook"
```

### Command reference

```bash
kairos init                                     # create .kairos/ and state.json
kairos dial "<task>" [--force-alpha|--force-beta|--force-gamma]
kairos scout [--all] [--save-spec]              # manifest reconnaissance
kairos spec <name>                              # 5-file delta spec
kairos worktree create|remove|list <name>
kairos mutate <file> --test "<cmd>" [--max-mutants N] [--timeout S]
kairos audit --base main [--worktree PATH|--root-only]
kairos archive <change_id>
kairos rollback [--worktree PATH|--root-only]
kairos status [--dashboard|--header-only]
kairos token import --usage <log.jsonl>
kairos lesson add|list
kairos registry
kairos export <claude|cursor|agents|universal|all>
kairos update [--skip-self-test]
```

---

## Repository layout

```text
kairos-framework/
├── RETRACTION.md              # what was claimed, why it was wrong
├── CLAIMS.md                  # every surviving quantitative claim + artifact
├── rules/kairos-core.md       # directives and the five iron laws
├── agents/                    # scout, critic, worker, auditor personas
├── skills/                    # 7 protocol skills (dial, spec, build, judge, …)
├── scripts/kairos_cli.py      # the zero-dependency CLI
├── tests/
│   └── fixtures/fraud_corpus/ # labelled diffs (fraud vs clean) + expected verdicts
├── benchmark/
│   ├── PREREGISTRATION.md     # written before data collection
│   └── case_study_gemini_n1/  # one real run, relabelled as a case study
└── docs/                      # architecture, lessons, opportunities
```

---

## Documentation

- [`RETRACTION.md`](RETRACTION.md) — the withdrawn claims and the mechanism behind each.
- [`CLAIMS.md`](CLAIMS.md) — the ledger. Every number in this repo needs a row.
- [`docs/OPPORTUNITIES.md`](docs/OPPORTUNITIES.md) — what parts of this are worth building for other people, and what is not.
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — how the pieces fit.
- [`docs/AGENT_LESSONS.md`](docs/AGENT_LESSONS.md) — behavioral heuristics, no performance claims.
- [`docs/case-studies/GEMINI_N1.md`](docs/case-studies/GEMINI_N1.md) — one run, both arms, including the design flaw.

---

## License

Apache License 2.0 — see [`LICENSE`](LICENSE).

Built by Ismael Soilet, with AI assistance. The AI assistance wrote some of the claims that had to be retracted; the retraction was written with the same tooling and checked against observed output.
