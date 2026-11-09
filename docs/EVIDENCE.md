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
| Best spec arm vs control, merge rate | 84% vs 72% | modest, real, within noise |
| No spec framework beat another | gaps ≤2pp, band ±10pp | **KAIROS claims no better format** |
| OpenSpec had the lowest spec drift | **2.4%** | the lowest of all arms — see §5 |
| OpenSpec merged the most | 42/50 | the reason §5 recommends it as the front end |
| Specs covering 6+ of 8 checklist items | merged **89.3%** vs **60.0%** | the 8-section template and the 6/8 threshold |
| Tickets with 3+ files | spec paid back | the fit test's primary question |
| Bug-fix, refactor, test-writing tickets | **0pp** gain, higher cost | the fit test says NO_SPEC for these |
| Spec phase cost | ~18 min median, 35.1% of tokens | quoted in the skill so the cost is visible |
| **Merged tickets that did not match their own spec** | **7.9%** | **the gap KAIROS exists to close** |
| Review defects per merged ticket | 0.46 with spec vs 0.86 without | specs reduce defects even where merge rate does not move |
| Median spec size | 128 lines | the "under ~130 lines" guidance |

**Correction, 2026-11-09.** An earlier version of this section said every
framework stops at approval. That was wrong: **OpenSpec has `/opsx:verify`**,
which checks the implementation against the change artifacts across three
dimensions (completeness, correctness, coherence) before archive. It is the one
framework in the benchmark that addresses post-build drift, and it does it with
the lowest measured drift of any arm (2.4% vs 4.9–12.5% for the others).

What `/opsx:verify` does not do, and why a second check still matters:

- It is **advisory**. Its own skill text says "Verification is advisory" and
  "archive retains its own checks". It produces a report; it does not fail a
  build. A report nobody blocks on is a report that gets skimmed.
- It verifies against **requirements and scenarios**, which is the right target,
  but by keyword search and inference — "search codebase for keywords related to
  the requirement".
- It has no notion of a **no-change list**, so an unrelated file rewritten in the
  same change is invisible to it.

`kairos gate` is therefore complementary rather than novel: it adds a hard exit
code, a declared-invariant check, and a completeness floor. OpenSpec's own
numbers (2.4% drift, 42/50 merged, lowest cost of the spec arms at $2.71) are the
reason §5 recommends using OpenSpec as the front end and the gate as the back.

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

## 4b. The four coding guidelines, and the correction about their source

**Source:** Andrej Karpathy's post of January 2026 on LLM coding pitfalls,
<https://x.com/karpathy/status/2015883857489522876>. The four guidelines are a
distillation of that post, packaged as one `CLAUDE.md` by
[multica-ai/andrej-karpathy-skills](https://github.com/multica-ai/andrej-karpathy-skills)
(231k stars) and mirrored at `forrestchang/andrej-karpathy-skills` with identical
content and identical install instructions.

**Correction.** An earlier answer in this project said there was no Karpathy
"list of principles" and that the attribution in `agents/kairos_worker.md` was
unsourced. That was wrong. The post exists, the four guidelines quote it
directly, and two independent secondary sources reproduce the quotes
([Addy Osmani](https://addyo.substack.com/p/the-80-problem-in-agentic-coding),
[AppSoftware timeline](https://www.appsoftware.com/blog/a-timeline-of-interesting-takes-on-agentic-ai-capability-in-software-engineering)).

**What the guidelines are not:** they are not Karpathy's own framework, they were
not written by him, and the repo is a community distillation. The README says
"derived from" and that is accurate. Treating it as an official specification
would be the same error as treating a popularity count as evidence.

**What this project does with them.** Three of the four were already enforced by
structure; one was not, and that is the one everyone nods at and nobody checks:

| Guideline | Enforced by | Was it checked before? |
| :--- | :--- | :--- |
| Think Before Coding | `kairos brainstorm --check` | no — added v1.2 |
| Simplicity First | `kairos gate`: unrequested dependency, oversized new file | no — added v1.2 |
| Surgical Changes | `kairos gate`: no-change list, scope drift | yes |
| Goal-Driven Execution | `kairos gate`: criteria must map to a test | yes |

The simplicity check is a **proxy, not a measurement**. It flags two shapes —
a dependency the spec never mentioned, and a new file more than 3x larger than
every other new file in the same change. It cannot tell whether code is
overcomplicated, and it is deliberately a `minor` finding that never blocks. A
false accusation of "too complex" costs more than a missed one.

---

## 4c. Live reconnaissance replaces a hardcoded list

An earlier version of `kairos scout` shipped a dictionary of packages with known
breaking changes. It rotted exactly like the training data it was meant to
correct: it named a major release as current that the registry had already
superseded twice.

The replacement queries npm, PyPI and crates at run time and reports the gap
between what a manifest declares and what exists. No version number in this
repository is stated from memory.

**Limit, stated plainly:** this catches *version* drift, which is mechanical and
verifiable. It does not catch an architectural trend, a new library that would be
a better fit, or a change in best practice. Those require reading, and a script
that claimed to detect them would be guessing. `kairos scout` is a version check,
not a research assistant, and it should not be sold as one.

---

## 4d. fable-judge and SureForge: what was kept, what was not adopted

Both are installed here and both are good. Neither was adopted as a framework,
because the useful part of each is four or five checks and the rest is process
vocabulary that this project already speaks.

### fable-judge, item by item

| Item it checks | Covered before | Now |
| :--- | :--- | :--- |
| Weakened checks | yes — `fraud:assert_deletion`, `fraud:weakened_test_skip` | same |
| Scope creep | yes — `scope_drift`, `no_change_violation` | same |
| Spec betrayal | yes — `spec_drift` | same |
| **Re-run every claimed verification** | no | **`--verify "<cmd>"`** |
| **Unauthorized action** | no | **`outward_command`** |
| **Debris** | no | **`debris`** |
| Verdict vocabulary | — | `READY`/`REPAIR`/`BLOCKED`, already in use here |

`--verify` is the important one. It is the only claim a diff cannot settle: run
the command, capture the real exit code, and block on failure. Without it the
gate prints `verification: NOT RUN — so 'tests pass' is a claim`.

`outward_command` flags `git push`, `npm publish`, `terraform apply`,
`kubectl delete`, `DROP TABLE`, `rm -rf /` and similar added in the diff. It is
`major`, not a blocker: adding a deploy script is often correct, but a reviewer
has to see it.

`debris` flags interactive debuggers as `major` (a `breakpoint()` in delivered
code halts execution) and scratch files / debug prints as `minor`. `print()` and
`console.error()` are deliberately **not** matched — they are legitimate output,
and flagging them is how a checker gets switched off.

### SureForge, item by item

| Rule | Where it lives here |
| :--- | :--- |
| Know the contract | the spec, scored for completeness |
| Advance on evidence | gate exit code |
| READY / REPAIR / BLOCKED | the gate's verdict vocabulary (adopted from SureForge) |
| Separate production from review | fresh-context review (EGM's Goldfish) |
| Coverage, not sampling | per-criterion drift check |
| Smallest sufficient tier | `kairos fit` |

SureForge contributed **the vocabulary** and nothing mechanical that was missing.
Its tiers, ledgers, three-round cap and resume protocol are process
prescriptions for a human working with an agent; this project does not enforce
them and does not claim to.

### What was deliberately not adopted

- **A second set of verdict names.** Two frameworks with `VERIFIED` and `READY`
  for the same idea is exactly the noise this is trying to remove.
- **Report formats.** fable-judge's claims table is good; the gate already
  produces one row per finding with its evidence.
- **The suite mode.** `/fable-judge suite` evaluates a skill or model against a
  trap suite. Useful, unrelated to delivery verification, and it needs the
  fable-method `eval/` directory.

### Correction to an earlier claim

An answer earlier in this project said fable-judge and SureForge were "already
covered" by the gate. **Three of seven items were.** The other four were not, and
saying so without checking was the same error this project keeps making. They are
implemented now, and the mapping above is the receipt.

---

## 5. The recommended stack, and why each piece is there

The benchmark makes one recommendation possible without any further measurement,
because the numbers are its own:

| Layer | Tool | Evidence for choosing it |
| :--- | :--- | :--- |
| Write and iterate the spec | **OpenSpec** | 42/50 merged (highest), 2.4% drift (lowest), $2.71 per merged ticket (second lowest), 12-minute median spec phase (fastest) |
| Review the spec before coding | **fresh-context reviewer** | reasoning, not measurement: same-context review inherits the author's blind spots. EGM's structure, credited |
| Decide whether to spec at all | **`kairos fit`** | 0pp gain on bug-fix/refactor/test tickets; no gain below 3 files |
| Verify the delivery | **`kairos gate`** | hard exit code and a no-change check, which `/opsx:verify` does not provide |

**One tool, not five.** OpenSpec owns the artifact lifecycle: propose, apply,
verify, archive. KAIROS does not duplicate any of it. It adds the two decisions
OpenSpec leaves open — *should this ticket have a spec* — and the hard failure
OpenSpec leaves advisory — *the diff touched a file the spec said not to touch*.

If OpenSpec's `/opsx:verify` later gains a blocking mode and an invariant check,
the gate becomes redundant and should be deleted. That is the honest condition
for its existence.

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
