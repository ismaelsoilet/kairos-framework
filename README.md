# KAIROS (καιρός)

### The checks a coding agent cannot do for itself

> **"The exact measure, at the opportune moment."**
>
> *kairos* is the Greek word for the right moment. The project earned the name
> badly for its first year. See the retraction notice below.

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-green.svg)](https://python.org)
[![Version: 1.3.0](https://img.shields.io/badge/Version-1.3.0-blueviolet.svg)](plugin.json)

---

> ## ⚠️ Retraction notice (2026-11-08)
>
> Versions up to v1.1.0 published token-savings percentages, success rates and
> "empirical benchmark" results on this page. **They were not measured.** They
> were constants written into the benchmark scripts and printed as observations.
>
> **All of them are withdrawn.** Read [`RETRACTION.md`](RETRACTION.md) for the
> full list, the mechanism behind each, and what was actually true.

**Languages:** English (this file) · [Português (Brasil)](README.pt-br.md)

---

## What this is

Four commands do something a model cannot do by reasoning:

| Command | Question it answers | Why a model can't |
| :--- | :--- | :--- |
| `kairos fit` | should this ticket have a spec at all? | it does not know your measured cost curve |
| `kairos brainstorm` | what did we reject, and what would prove this wrong? | it forgets the conversation it had |
| `kairos gate` | does the diff match the approved spec? | the spec is outside its context |
| `kairos audit` | did the change weaken a test? | it is a claim, not an observation |

`init` and `spec` are scaffolding.

It does not generate code, call a model, or pick a model. It is the part that
refuses to take the agent's word for it.

**v1.3 removed the rest.** The Elastic Dial, four agent personas, nine lifecycle
stages, git worktrees, mutation testing, harness exports, an extension registry,
in-repo lessons and a self-update engine were all deleted. None had evidence
behind it, and the classifier in particular made confident decisions it could not
justify. Their sixteen documents are in [`docs/archive/`](docs/archive/), not
deleted — deleting a document that made a claim is how the claim disappears.

`kairos scout` also went. It queried npm, PyPI and crates for live version gaps,
which was genuinely useful, but that belongs in a dependency tool rather than
here. It is recoverable from git history at tag `pre-prune`.

---

## The cycle

```bash
kairos fit --touches 4 --criteria 5      # should this even have a spec?
kairos brainstorm --new dark_mode        # three alternatives, and a falsifier
openspec propose dark-mode               # the spec (OpenSpec owns this)
# ... implement ...
kairos gate --spec openspec/changes/dark-mode/specs/ui/spec.md \
            --base main --verify "pytest -q"
```

Exit code is `0` only on READY, so it drops into a pre-push hook.

---

## What the gate checks

| Check | Verdict |
| :--- | :--- |
| Spec covers fewer than 6 of 8 measured sections | **BLOCKED** |
| A file on the no-change list was modified | **BLOCKED** |
| `--verify "<cmd>"` exits non-zero, or times out | **BLOCKED** |
| Files touched that the spec never named | REPAIR |
| Acceptance criteria with no test in the diff | REPAIR |
| An interactive debugger (`breakpoint()`, `pdb`) added | REPAIR |
| `git push`, `npm publish`, `terraform apply` added | REPAIR — needs authorization |
| Test deletion or weakened tests | REPAIR |
| A dependency the spec never mentioned | minor |
| A new file 3x larger than every other new file | minor |

Without `--verify`, the report prints `verification: NOT RUN — so 'tests pass' is
a claim`. It does not imply the tests ran.

`brainstorm` refuses a brief with fewer than three alternatives, with an
alternative that has no rejection reason, or with no "what would make this wrong"
section. A spec with no recorded alternatives is not a decision.

### What it does not do

- It compares **words, not meaning**. A test named after a criterion but asserting
  nothing passes the drift check.
- It does **not run your tests** unless you give it `--verify`.
- It cannot tell an intentional deletion from a fraudulent one.
- Three scanner rules ship **off by default** (measured precision 0–17%).
- It reads English and Portuguese specs. Other languages score low, and that is a
  limitation of the checker, not a judgment on the spec.

---

## The scanner's measured record

An independent probe of eight fraud patterns caught three against v1.1.0. Over
**370 real merged pull requests** from 12 open-source projects, with 75 flags
adjudicated individually:

| Rule | Wave 1 | Wave 2 |
| :--- | ---: | ---: |
| `assert_deletion` | 71% | **100%** |
| `weakened_test_skip` | 89% | 67% |
| `silent_failure_empty_catch` | 17% | **0%** |
| `guard_removal` | **0%** | **0%** |
| `phantom_stub` | **0%** | **0%** |

The pattern is not subtle: the two rules that **count** things work. The three
that **recognize a shape** in one line do not, because the shape is ambiguous
without structural context.

With the default set, the scanner detects **6 of 24 fraud cases (25%)** in its own
corpus, with zero false positives on the 19 clean ones. It is precise when it
fires and it fires rarely. **It is not a security gate.**

Full accounting, including what was thrown away:
[`docs/EXTERNAL_VALIDATION.md`](docs/EXTERNAL_VALIDATION.md).

---

## Install

Requires Python 3.10+. No dependencies.

```bash
git clone https://github.com/ismaelsoilet/kairos-framework
cd your-project
python3 /path/to/kairos-framework/scripts/kairos_cli.py init
```

### In CI

[`examples/github-actions/kairos-gate.yml`](examples/github-actions/kairos-gate.yml)
runs the gate on every pull request and fails when the verdict is not READY. It
needs `fetch-depth: 0`, because the gate diffs against the base branch.

`gate --json` writes one parseable document to stdout and its progress to stderr,
so `gate --json > out.json` works.

### Command reference

```bash
kairos init                                    # create .kairos/
kairos fit --touches N --criteria N [--crosses-boundary] [--changes-schema-or-api]
kairos brainstorm --new <name> | --check <path>
kairos spec <name>                             # eight-section spec
kairos gate --spec <path> [--base main] [--verify "<cmd>"] [--json]
kairos audit [--base main] [--enable-rule NAME]
```

---

## Repository layout

```text
kairos-framework/
├── RETRACTION.md                  # what was claimed, why it was wrong
├── CLAIMS.md                      # every surviving claim + its artifact
├── scripts/
│   ├── kairos_cli.py              # the CLI
│   ├── kairos_gate.py             # spec <-> diff verification
│   └── kairos_brainstorm.py       # alternatives before commitment
├── tests/
│   ├── test_gate.py
│   ├── test_brainstorm.py
│   └── fixtures/fraud_corpus/     # labelled diffs + expected verdicts
├── skills/kairos/SKILL.md         # the agent-facing protocol
├── agents/kairos_critic.md        # zero-context reviewer
├── rules/kairos-core.md           # the five iron laws
└── docs/
    ├── EVIDENCE.md                # read first: every rule and its source
    ├── EXTERNAL_VALIDATION.md     # 370 PRs, adjudicated
    ├── OPPORTUNITIES.md           # what is worth building, what is not
    └── archive/                   # the v1.2 lifecycle, kept as a record
```

---

## Documentation

- [`docs/EVIDENCE.md`](docs/EVIDENCE.md) — **read this first.** Every rule traced to a source, with that source's limits, and what is not treated as evidence.
- [`docs/EXTERNAL_VALIDATION.md`](docs/EXTERNAL_VALIDATION.md) — 370 real merged PRs, 75 flags adjudicated, and which rules survived.
- [`RETRACTION.md`](RETRACTION.md) — the claims withdrawn in v1.2 and the mechanism behind each.
- [`CLAIMS.md`](CLAIMS.md) — the ledger. Every number needs a row with an artifact.
- [`docs/OPPORTUNITIES.md`](docs/OPPORTUNITIES.md) — what parts of this are worth building for others, and what is not.

Sixteen documents describing the v1.2 lifecycle moved to [`docs/archive/`](docs/archive/)
when that lifecycle was removed in v1.3, including the single-run Gemini case
study.

---

## It is a back end, not a framework

Use **one** spec tool from start to finish — OpenSpec is the measured best choice
(42/50 merged, 2.4% drift, fastest spec phase at 12 min). `kairos gate` sits
behind it, and behind EGM, Spec Kit or KAIROS layouts alike.

It does not replace your spec tool and does not claim its format is better: the
benchmark found no meaningful difference between any of them (±10pp noise band).

---

## License

Apache License 2.0 — see [`LICENSE`](LICENSE).

Built by Ismael Soilet, with AI assistance. The AI assistance wrote some of the
claims that had to be retracted; the retraction was written with the same tooling
and checked against observed output.
