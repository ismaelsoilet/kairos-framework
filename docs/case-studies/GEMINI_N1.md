# Case study: one governed run vs one free run (n = 1 per arm)

**Read this first:** the two arms of this run were given **different tasks**.
The governed arm's requirements named the mechanism (`AsyncMutex`, "preventing
race conditions"); the free arm's requirements did not mention concurrency at
all. Any difference below is therefore explained just as well by the prompt as
by the framework. **This is not evidence that KAIROS saves tokens.** It is a
record of what happened once, preserved because the raw transcripts are real and
because deleting inconvenient data is how the original claims went wrong.

A properly designed version of this comparison is specified in
[`benchmark/PREREGISTRATION.md`](../PREREGISTRATION.md) and has not been run.

---

## What was actually measured

Two agent sessions, transcripts preserved verbatim in
`benchmark/case_study_gemini_n1/`, both on the same model and the same day.

| Metric | Free arm | Governed arm |
| :--- | ---: | ---: |
| Input tokens | 102,897 | 69,589 |
| Output tokens | 9,422 | 21,087 |
| **Active (in + out)** | **112,319** | **90,676** |
| Cache read | 500,762 | 319,139 |
| Total processed | 613,081 | 409,815 |
| LLM steps | 13 (turn 1) + 6 (repair) | 16 |
| Permission retries | 0 | 9 |

Source: `python3 benchmark/case_study_gemini_n1/run_real_gemini_benchmark.py`,
which parses the two JSONL transcripts and prints the table above. The numbers
are real API usage, not local estimates.

## What the numbers do and do not show

**Do:** the governed arm's output was larger (21,087 vs 9,422) — it wrote a spec
and a test suite — while its input was smaller. Its total cycle was shorter by
21,643 active tokens despite that.

**Do not:** show that the process caused the difference. Three confounds are
enough to explain it on their own:

1. **Different requirements.** Only one arm was told about concurrency.
2. **A repair cycle on one side.** The free arm's turn 2 exists because its
   implementation failed a load test. That failure is the interesting event,
   but the assignment of the hazard warning is what caused it.
3. **n = 1.** One run per arm. No repetitions, no interval, no order
   randomisation.

A fourth point that was previously reported as a win and is not one: the
governed arm burned **2.2× the output tokens** and needed **9 permission
retries**. Those were folded into its total and described as "operational".
They belong in the cost column, which is where they are now.

## What did reproduce

The physical concurrency result is real and independent of the prompts'
fairness. `evaluate_live_gemini.js` runs both wallet implementations:

- free-arm implementation: 60 concurrent withdrawals of 10 from 500 →
  **60 successes, final balance −R$ 100** (overdraft);
- the same implementation after its repair cycle → 50 successes, 10 rejections,
  final balance 0;
- governed-arm implementation → 50 successes, 10 rejections, final balance 0,
  first pass.

The mutex does what it says. The open question was never whether a mutex works;
it is whether adding a process makes an agent reach for one more reliably than a
well-written requirement does. Nothing here answers that.

## Why keep it

Because it is the only run in this repository with real, reproducible token data,
and because the failure mode it demonstrates is worth knowing: **a prompt that
names the hazard dominates any framework layered on top of it.** If that is true
generally, it is more useful to publish than another unverified savings figure.

## Reproduce

```bash
cd benchmark/case_study_gemini_n1
python3 run_real_gemini_benchmark.py   # prints the token table and runs the JS lab
node evaluate_live_gemini.js           # concurrency check on both implementations
```

The transcripts are read from the paths recorded at the top of
`run_real_gemini_benchmark.py`. If those files are absent on your machine, the
token table cannot be reproduced — only the concurrency lab can.
