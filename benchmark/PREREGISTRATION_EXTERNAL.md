# Pre-registration — external validation of the fraud scanner

**Status:** written 2026-11-08, **before any external diff was scanned**.
**Data collected so far: none.**

This is the validation the internal corpus could not provide. The corpus in
`tests/fixtures/fraud_corpus/` was written by the same person who wrote the
rules and then iterated against them. Its 100% recall is a regression number,
not evidence of generalisation. A clean holdout scored 6/8. This study measures
the scanner against code nobody involved wrote, for a real purpose.

---

## 1. Question

When `scan_diff_text()` runs over real merged pull-request diffs from public
open-source repositories, **how often is it wrong?**

Two failure directions matter, and they are not symmetric:

- **False positive** (flags clean code): wastes a maintainer's time and gets the
  tool uninstalled. Measurable directly by adjudicating every flag.
- **False negative** (misses fraud): the tool silently fails its only purpose.
  **Not directly measurable**, because no external diff carries a "this is
  fraud" label. Estimated separately, see §5.

---

## 2. Sampling rule — fixed before looking

Repositories are a **convenience sample** of popular, actively-merged projects,
chosen for language coverage and PR volume. This is not a random sample and the
report must say so. The list is fixed now and will not change after results:

| # | Repository | Why it is here | Language |
| :--- | :--- | :--- | :--- |
| 1 | `psf/requests` | Python, heavy test suite, long history | Python |
| 2 | `pallets/flask` | Python, disciplined review culture | Python |
| 3 | `pytest-dev/pytest` | Python, tests are the product | Python |
| 4 | `expressjs/express` | JS, small codebase, many merges | JavaScript |
| 5 | `axios/axios` | JS, large test suite | JavaScript |
| 6 | `sindresorhus/got` | TS/JS, strict test conventions | TypeScript |
| 7 | `chalk/chalk` | JS, minimal, well-tested | JavaScript |
| 8 | `psf/black` | Python, formatter with golden tests | Python |

**PR selection:** from the default branch history, take merge commits in
chronological order, and sample with a **fixed stride** so the choice cannot be
influenced by content. Stride is computed as `max(1, total_merges // 40)` per
repository, targeting ~40 PRs per repo. The diff for each PR is
`<merge>^1...<merge>` — first parent to merge, which is what the PR introduced.

**Exclusions, declared now:** merges with no diff, merge commits from automated
bots (dependabot, pre-commit-ci), and diffs over 5,000 changed lines (they are
usually generated lockfiles or vendored code). Excluded merges are counted and
reported.

---

## 3. Adjudication rule

Every flag the scanner produces is adjudicated by me, reading the actual diff
context. Each flag gets exactly one verdict:

| Verdict | Meaning |
| :--- | :--- |
| `TRUE_POSITIVE` | The diff genuinely weakens verification, hides failure, or adds dead code. A careful reviewer would object. |
| `FALSE_POSITIVE` | The pattern is present but legitimate in context (e.g. a mocked external API, a deliberate retry, a test asserting an exception is raised). |
| `UNRELATED` | The scanner matched the wrong thing entirely (e.g. matched a string inside a comment or a fixture). |

The adjudication is done **after** seeing the flag, which introduces bias. To
limit it, every `FALSE_POSITIVE` and `UNRELATED` verdict must quote the
surrounding diff lines that justify it. A verdict without a quote is not
accepted. Where a judgment call is genuinely 50/50, the verdict is recorded as
`FALSE_POSITIVE` — the scanner is assumed wrong when uncertain.

**Limitation stated up front:** I am both the author of the scanner and the
adjudicator. This is not independent review. What it does control for is the
one thing the internal corpus could not: the diffs are not mine, and I have no
memory of writing them.

---

## 4. Metrics

- **Flag rate**: flagged PRs / PRs scanned. The practical question for adoption
  is "how often does this interrupt me".
- **Precision**: `TRUE_POSITIVE / (all flags)`. Directly measured.
- **Precision by fraud type**: some rules will be better than others; the
  breakdown decides which to keep.
- **Language breakdown**: a Python-heavy rule set should show up here.

Reported with raw counts, never only percentages. Every flag gets a row in a
published CSV with repo, PR, file, line, fraud type, verdict, and quote.

---

## 5. Recall — what can and cannot be measured

Recall cannot be measured directly. Two partial estimates are attempted, both
declared now:

**R1 — test-deletion recall.** Search the sampled PRs for the objective signal
"a test file lost assertion lines or test functions" by diff arithmetic alone
(independent of the scanner), then check whether the scanner flagged those same
PRs. This measures whether the scanner catches the one class that is
mechanically detectable.

**R2 — mutation-style injection.** Take N=30 *merged, accepted* diffs, inject a
known fraud pattern into each (weaken an assertion, swallow an exception), and
confirm the scanner flags the mutated version while leaving the original clean.
This measures detection ability on real code shapes, but the injection is still
authored by me. It is a stronger test than the internal corpus because the
surrounding code is real.

Both are labelled as estimates, not recall.

---

## 6. What would invalidate this study

Declared in advance:

- Adding a repository to the list after seeing its results.
- Changing the stride to avoid or include specific PRs.
- Reclassifying a flag as `FALSE_POSITIVE` after the precision number is known
  without recording the quote that justified it.
- Reporting a percentage without the raw counts.
- Claiming any recall figure from R1/R2 as if it were measured recall.

---

## 7. Expected outcome (recorded so it can be wrong)

My prediction, written before running: **precision between 30% and 60%** on
external diffs, considerably worse than the 96% internal figure. The reason is
structural — the internal corpus tests patterns in isolation, while real diffs
contain mocks of external services, deliberate retries, and test helpers that
look like fraud to a line-oriented rule.

If precision comes out above 80%, I will treat that as surprising and look for a
bug in the harness before believing it.
