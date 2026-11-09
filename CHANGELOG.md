# Changelog

All notable changes to this project. Versions before 1.2.0 are recorded here for
the record; their published metrics are retracted (see [`RETRACTION.md`](RETRACTION.md)).

## [1.3.0] — 2026-11-09

A breaking release. Everything without evidence behind it was deleted.

### Removed

The Elastic Dial, nine lifecycle stages, git worktree isolation, mutation
testing, harness exports, the extension registry, in-repo lessons, the
self-update engine, token telemetry, rollback, archive and status. Also
`kairos scout`: its live dependency check was useful but belongs in a dependency
tool. Recoverable from git tag `pre-prune`.

Seven of eight skills and three of four agents. Six stale living specs and the
old `.kairos/changes` artifacts.

Fifteen documents moved to [`docs/archive/`](docs/archive/) rather than being
deleted. A document that made a claim should stay visible after the claim is
retracted; the same holds for a design removed because it had no evidence.

### Changed

`kairos_cli.py`: 2,396 lines → ~1,150. Six commands remain — `init`, `fit`,
`brainstorm`, `spec`, `gate`, `audit` — and every one is covered by a test that
runs it the way a user does.

### Fixed

- `CODE_EXTENSIONS`, `DOC_EXTENSIONS` and `FRAUD_PATTERNS` were inside a deleted
  block, so the scanner crashed on every call until they were restored.
- Two help strings still pointed at `kairos worktree create` and `kairos mutate`.

### Kept, with reasons

| Command | Why it survives |
| :--- | :--- |
| `fit` | the benchmark measured 0pp gain on bugfix/refactor tickets at ~18 min cost |
| `brainstorm` | OpenSpec's explore has no mandatory artifact; nothing records the rejected options |
| `gate` | 7.9% of merged spec tickets did not match their own spec |
| `audit` | only the two rules with measured precision above 67% run by default |

## [1.2.0] — 2026-11-08

The release that removes claims the project could not support, and fixes the
tool that was supposed to catch exactly that kind of claim.

### Added

- `RETRACTION.md` — every withdrawn claim, the mechanism that produced it, and
  what was actually true. Written in English and Portuguese.
- `CLAIMS.md` — a ledger of every quantitative claim with a status vocabulary,
  a reproducible artifact, and a command. A number without a row is a defect.
- `tests/fixtures/fraud_corpus/corpus.json` — 43 labelled diffs (24 fraud, 19
  clean) with expected verdicts, plus `benchmark/eval_corpus.py` to score the
  scanner against it. Current: recall 100%, precision 96%, one known FP.
- `benchmark/PREREGISTRATION.md` — hypotheses (including H0, that KAIROS may
  cost more), three arms with identical task text, a mandatory hint-control
  arm, n = 5, bootstrap CI, blind judging, and the decision rule fixed before
  any data collection. Status: blocked, nothing run.
- `docs/case-studies/GEMINI_N1.md` — the single real run, kept as a case study
  with the design flaw stated first.
- `docs/OPPORTUNITIES.md` — three candidate directions with the evidence each
  would need, and an explicit list of what is not an opportunity.
- Scanner detections: `weakened_assertion` (paired removed/added comparison),
  `mock_substitution` (including `jest.spyOn`), `unconditional_accept`,
  `guard_removal` (including boundary loosening).
- `kairos audit --allow-file PATH` — explicit, reported exclusions.
- `kairos token import --usage <log.jsonl>` — reads real input/output/cache
  token counts and cost from a harness log, stores the source hash.
- `LICENSE` — Apache-2.0. The badge existed since v1.0; the file did not.
- Tests for the token import contract, the mutation gate, the dial override,
  and the worktree create/remove lifecycle. Suite: 37 → 40 tests.

### Changed

- `kairos audit` no longer grants `VERIFIED` on a clean diff alone. It requires
  a `kmutant_latest.json` with zero survivors; otherwise the verdict is `REPAIR`.
  Gate vocabulary is now `READY` / `REPAIR` / `BLOCKED`.
- `kairos dial`: `--force-beta` and `--force-gamma` are evaluated before keyword
  scores, so an explicit override wins. It previously lost silently.
- `kairos status` prints `Spent: UNMEASURED` until a usage log is imported,
  instead of printing a zero that reads as "no tokens were spent".
- `kairos mutate` counts timeouts separately and excludes them from the kill
  score. A hanging mutant is not evidence that the test caught it.
- `kairos status --dashboard` treats `REPAIR_REQUIRED` and `ROLLED_BACK` as real
  stages; they previously rendered as 0% `IDLE`, hiding a failure state.
- `benchmark/runner.py` → `benchmark/projection_runner.py`, and
  `benchmark/kbench_multi_llm/` → `benchmark/simulation_multi_llm/`. Both now
  print what they are: a projection and a simulation, neither measuring anything.
- `benchmark/real_gemini_benchmark/` → `benchmark/case_study_gemini_n1/`.
- `plugin.json` gains `id` and `repository` (both were already assumed by
  `kairos update`'s repo detection).
- READMEs rewritten. Result badges removed. Capabilities split into
  implemented/tested, implemented/untested, and documented-but-not-implemented.

### Removed

- `kairos token add <n>` — the agent incrementing its own counter is the exact
  false-completion pattern this project claims to detect.
- The scanner's self-exclusion (`if current_file.endswith("kairos_cli.py")`),
  which made it impossible for the tool to audit the tool.
- The "Audit Verdict: VERIFIED" and "Gemini 3.8 Savings: 19.3%" badges.
- `kairos drift` references from `kairos-sync` and `AGENT_LESSONS`. The
  subcommand never existed; the docs now say NOT IMPLEMENTED.
- Five lines of unreachable code after a `return` in `cmd_mutate`.

### Retracted

- "55% total token savings", "20%/95%/98% success rates",
  "~46.7%/~3.8%/0.0% fraud escape" — constants in the projection script.
- "Multi-LLM benchmark across 6 models with real BPE" — no model was called;
  the same literal strings were tokenized six times.
- "51% to 68% economy" — an invented `* 18` multiplier.
- "19.3% net hardware token savings", "100% zero-defect first pass",
  "33.15% with cache read" — arithmetic was real, the comparison was not: the
  two arms received different tasks.
- "Peer-reviewed", "independent audit", "certification", "9.4/10".
- "All 18 vulnerabilities 100% neutralized" — 13 of 20 items have a test that
  fails without the fix; the rest are listed as gaps.

## [1.1.0] and earlier

See `RETRACTION.md`. The CLI, the atomic state writes, the path-traversal
defenses and the concurrency lab were real and still are. Most of the metrics
published alongside them were not.
