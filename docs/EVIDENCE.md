# EVIDENCE — what this project's rules are based on

Every rule in the KAIROS skill traces to one of four sources. If a rule has no
source here, it is an opinion and should be labeled as one.

---

## 1. Spec-driven development: a controlled benchmark

**Source:** [Uvik Software SDD Benchmark 2026](https://uvik.net/blog/spec-driven-development-benchmark/),
Q4 2026 run, published 2026-11-02. Method: 50 brownfield production Python
tickets, same model (`claude-sonnet-5`) in every arm, same repositories, same
45-minute time boxes, blind senior review, a no-spec control arm, and a noise band
of ±10 percentage points computed from 10 re-run tickets. Raw data under CC BY 4.0.

**What it found, and what this project takes from it:**

| Finding | Number | Consequence in KAIROS |
| :--- | :--- | :--- |
| Best spec arm vs control, merge rate | 84% vs 72% | modest, real, and within the noise band of each other |
| No spec framework beat another | gaps ≤2pp, band ±10pp | **KAIROS does not claim its spec format is better than Spec Kit, Kiro, BMAD or OpenSpec** |
| Specs covering 6+ of 8 checklist items | merged **89.3%** vs **60.0%** | the 8-section template and the 6/8 gate threshold |
| Tickets with 3+ files | spec paid back | the fit test's primary question |
| Bug-fix, refactor, test-writing tickets | **0pp** gain, higher cost | the fit test says NO_SPEC for these |
| Spec phase cost | ~18 min median, 35.1% of tokens | quoted in the skill so the cost is not hidden |
| **Merged tickets that did not match their own spec** | **7.9%** | **this is the gap KAIROS exists to close** |
| Review defects per merged ticket | 0.46 with spec vs 0.86 without | specs reduce defects even where merge rate does not move |
| Median spec size | 128 lines | the "under ~130 lines" guidance |

**The one thing nobody else in that benchmark does:** every framework stops at
approval. None of them checks, after the build, that the delivered code matches
the approved spec. The benchmark measured that drift at 7.9% and left it
unaddressed. That check is what `kairos gate` is.

**Limits of this source, stated plainly:**

- One team ran it. Engineers had used the frameworks but not for equal time.
- Python only. Does not transfer to TypeScript, Java or Go without a new run.
- One model. A different model can change the gaps.
- Kiro ran in its own IDE; the other arms ran in Claude Code, so harness differs.
- It measures spec-first use only, not the long-term value of a living spec.
- It is vendor research (Uvik sells AI engineering services). It has a control
  arm and blind review, which the alternatives lack, and it publishes its raw
  data and limitations. Read it with that in mind.

---

## 2. Fresh-context review: a method, not a measurement

**Source:** [Google Open Source Blog, 2026-10-22](https://opensource.googleblog.com/2026/10/introducing-elephant-goldfish-model-plugin.html)
and [github.com/google/elephant-goldfish-model](https://github.com/google/elephant-goldfish-model)
(Apache-2.0, 15.4k stars, plugin for Antigravity, Claude Code, Codex, Cursor).

The Elephant-Goldfish Model: an "Elephant" session holds long-horizon project
context and writes the spec; stateless "Goldfish" sessions review it with no
memory of the conversation, across three gates — comprehension, antagonistic
review, implementation readiness.

Google states that "thousands of Googlers use this plugin every day to ship
production Google code." **That is a claim from the authors, with no published
measurement.** There is no controlled study, no merge-rate number, no defect
count.

**What KAIROS takes from it:** the review *structure* — three questions in a fixed
order, asked from a context that shares no blind spots with the author. This is
sound reasoning about why same-context review fails, and it costs nothing to
apply.

**What KAIROS does not claim:** that it improves merge rate or quality. That has
not been measured, by Google or here.

**What KAIROS adds:** EGM stops at approval. It reviews the *document* five
times and never opens the diff afterwards. The 7.9% drift figure from source 1 is
exactly what survives that gap.

---

## 3. Self-report is unreliable: a randomized controlled trial

**Source:** [METR, *Measuring the Impact of Early-2025 AI on Experienced
Open-Source Developer Productivity*](https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/),
July 2025. 16 experienced developers, 246 tasks in their own mature repositories,
randomized controlled trial.

**Findings:**

- Developers were **19% slower** with AI tools than without.
- They **believed** they had been **20% faster**.
- That is a 39-percentage-point gap between perception and measurement.
- Even after seeing the result, many expected to be faster next time.

**Consequence in KAIROS:** no rule in this project accepts an agent's statement
that work is complete. The two rules that never turn off are both consequences of
this study: claims are not evidence, and certainty is a signal to check harder.

**Limit:** it measured experienced developers on mature repositories in early
2025. It does not say AI never helps. It says the feeling of speed is not
evidence of speed — which is the only claim KAIROS relies on.

---

## 4. Which fraud detectors work: this project's own external validation

**Source:** [`docs/EXTERNAL_VALIDATION.md`](EXTERNAL_VALIDATION.md) — 370 real
merged PRs from 12 open-source repositories, pre-registered sampling rule,
75 flags adjudicated individually against the actual diff.

| Rule | Wave 1 precision | Wave 2 precision | Status |
| :--- | ---: | ---: | :--- |
| `assert_deletion` | 71% | **100%** | on |
| `weakened_test_skip` | 89% | 67% | on |
| `silent_failure_empty_catch` | 17% | **0%** | **off** |
| `guard_removal` | **0%** | **0%** | **off** |
| `phantom_stub` | **0%** | **0%** | **off** |

The pattern: rules that **count** removed assertions and tests work. Rules that
**recognise a shape** in one line do not, because `raise NotImplementedError` in
an abstract interface and `except ImportError: pass` for an optional import are
correct code that looks like fraud to a regex.

With the default set, the scanner detects 25% of the fraud cases in its own
corpus with zero false positives on the clean ones. It is a narrow signal, not a
gate on its own — which is why the gate's primary checks are spec completeness,
no-change violations and scope drift, not fraud patterns.

**Limit:** the same person wrote the scanner and adjudicated the flags. The diffs
are not his, which is what the internal corpus could not offer. Full statement in
the report.

---

## What is not evidence, and is not used

- **LLM self-assessment** of its own work. The RCT above is why.
- **Benchmarks where one arm received the solution in the prompt.** This project
  published one of those and retracted it; see [`RETRACTION.md`](../RETRACTION.md).
- **Star counts, vendor claims, "thousands of engineers use it"** — including
  Google's, above. Popularity is adoption, not efficacy.
- **Comparisons that did not run both sides.** If another framework was not
  executed on the same tickets, KAIROS says nothing about which is better.

---

## What would change these rules

| If this were measured | Then |
| :--- | :--- |
| EGM or Spec Kit + a diff gate beats KAIROS + a diff gate | use theirs; the gate is the contribution, not the format |
| Fresh-context review shows no effect on defects | drop Step 2 |
| Drift after merge is measured below 2% in practice | lower the priority of the gate |
| A rule's external precision rises above 80% | turn it back on |

Each of these is a test someone can run. None of them requires trusting this
document.
