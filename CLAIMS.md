# CLAIMS.md — Ledger of quantitative claims

**Rule:** any number that appears in a README, doc, badge, or code comment in this repository must have a row here. A number without a row is a defect, not a claim.

**Status vocabulary:**

| Status | Meaning |
| :--- | :--- |
| `MEASURED` | Produced by a versioned script, reproducible with a stated command, from data collected after this ledger existed. |
| `CASE_STUDY` | From a real run, n = 1 unless stated. Illustrates a mechanism. Does not generalize. |
| `ESTIMATE` | Deliberate planning figure with a stated basis. Not a result. |
| `UNVERIFIED` | Asserted but not reproducible in this repository. |
| `RETRACTED` | Was published as a result; was not one. Withdrawn — see `RETRACTION.md`. |

**Current state (v1.2.0): there are zero `MEASURED` rows.** That is the honest state of the project. The scanner corpus and the pre-registered benchmark are the two paths to changing it.

---

## Live claims

| claim_id | file | text | value | type | artifact | command | date | status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| C-001 | `tests/` | Test suite passes | 37 tests, exit 0 | MEASURED | `tests/test_cli_features.py` | `python3 -m unittest tests/test_cli_features.py` | 2026-11-08 | MEASURED |
| C-002 | `README.md` | Scanner detects 3 of 8 probed fraud patterns | 3/8 | MEASURED | probe transcript in `RETRACTION.md` | manual probe, see RETRACTION.md table | 2026-11-08 | MEASURED |
| C-003 | `README.md` | Scanner does not catch 5 named pattern classes | list of 5 | MEASURED | same probe | same probe | 2026-11-08 | MEASURED |
| C-004 | `benchmark/case_study_gemini_n1/` | Vibe arm active tokens | 112,319 (102,897 in + 9,422 out) | CASE_STUDY | `benchmark/case_study_gemini_n1/run.py` over two preserved transcripts | `python3 benchmark/case_study_gemini_n1/run.py` | 2026-11-08 | CASE_STUDY |
| C-005 | `benchmark/case_study_gemini_n1/` | KAIROS arm active tokens | 90,676 (69,589 in + 21,087 out) | CASE_STUDY | same | same | 2026-11-08 | CASE_STUDY |
| C-006 | `benchmark/case_study_gemini_n1/` | KAIROS arm output tokens vs vibe arm | 21,087 vs 9,422 (2.2×) | CASE_STUDY | same | same | 2026-11-08 | CASE_STUDY |
| C-007 | `benchmark/case_study_gemini_n1/` | KAIROS arm permission retries | 9 | CASE_STUDY | same | same | 2026-11-08 | CASE_STUDY |
| C-008 | `README.md` | Corpus recall and precision | **not yet measured** | — | `tests/fixtures/fraud_corpus/` + `benchmark/eval_corpus.py` | `python3 benchmark/eval_corpus.py` | pending | UNVERIFIED |
| C-009 | `README.md` | Bundle-size / runtime of scanner | **not yet measured** | — | — | — | pending | UNVERIFIED |
| C-010 | `README.md` | Benchmark hypotheses H1/H0 | **no data collected** | — | `benchmark/PREREGISTRATION.md` | — | pending | UNVERIFIED |

Claims C-008 through C-010 are intentionally listed as `UNVERIFIED` rather than omitted: they are the three things a reader is most likely to ask about, and the honest answer today is "not measured".

---

## Retracted claims

Full narrative in [`RETRACTION.md`](RETRACTION.md). Compact index here so the ledger is complete.

| claim_id | former text | former status | mechanism | status now |
| :--- | :--- | :--- | :--- | :--- |
| R-001 | "55% Total Savings" | presented as measured | hardcoded `kairos_budget` vs `min_tokens_monolith` in `benchmark/runner.py` | RETRACTED |
| R-002 | "20% / 95% / 98% success rates" | presented as measured | literal `vibe_pass` / `mono_pass` / `kairos_pass` in `runner.py` | RETRACTED |
| R-003 | "~46.7% / ~3.8% / 0.0% fraud escape" | presented as measured | literal print string in `runner.py` | RETRACTED |
| R-004 | "Fraud Detection Score 3/3 (100%)" | presented as measured | three synthetic diffs authored alongside the regexes | RETRACTED |
| R-005 | "Multi-LLM benchmark, 6 models, real BPE" | presented as measured | no API call in `kbench_multi_llm/runner.js`; string literals tokenized | RETRACTED |
| R-006 | "51%–68% economy across models" | presented as measured | `vibeReworkTokens * 18` invented multiplier | RETRACTED |
| R-007 | "19.3% net hardware token savings" | presented as measured result | arithmetic real; arms given different tasks (concurrency hint only in KAIROS arm); n=1 | RETRACTED as a result; retained as CASE_STUDY (C-004…C-007) |
| R-008 | "100% zero-defect first pass" | presented as measured | consequence of R-007's asymmetric prompts | RETRACTED |
| R-009 | "33.15% savings with cache read" | presented as measured | same arithmetic, different denominator; not a like-for-like comparison | RETRACTED |
| R-010 | "Peer-reviewed" | presented as fact | no peer review took place | RETRACTED |
| R-011 | "Independent audit / Zero-Trust VERIFIED" | presented as certification | same author, same machine, author-written prompt | RETRACTED |
| R-012 | "18 critical vulnerabilities neutralized" | presented as verified | no test-per-item mapping in the report | RETRACTED |
| R-013 | "85% / 60% token savings by mode" | presented as characteristic | no measurement behind the mode budgets | RETRACTED |
| R-014 | "570k tokens burned by monolith" | presented as measured | sum of hardcoded scenario budgets | RETRACTED |

---

## How to add a claim

1. Produce the artifact first. Script committed, command documented, raw output preserved.
2. Add the row with `status = MEASURED` **only** if a third party can re-run it and get the same number. Otherwise the highest status available is `CASE_STUDY` or `ESTIMATE`.
3. If the claim is in a README, it must link to this row.
4. If a claim is retracted, move it to the retracted table. Do not delete the row — deletion is how the original mess started.
