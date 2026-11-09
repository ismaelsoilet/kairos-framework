# Evidence Audit Table: KAIROS v1.1.0

> **Status as of v1.2:** rows 4 and 5 below were **retracted** on 2026-11-08.
> This file is kept as a historical record of what the release evidence looked
> like at the time, with the retraction applied in place. See `RETRACTION.md`.

| Check | Requirement | Command / Evidence | Status |
| :--- | :--- | :--- | :--- |
| 1 | Automated Test Suite | `python3 -m unittest discover tests` (37 tests) | ✅ PASS (Exit 0) — still true |
| 2 | Version Bump | `python3 scripts/kairos_cli.py -h` displays v1.1.0 | ✅ PASS — still true |
| 3 | Multiline Scanner Fix | Does not flag JSON/Markdown with catch strings | ✅ PASS — still true |
| 4 | ~~Independent External Audit~~ | ~~Verified by Command Code (DeepSeek v4.1 Flash)~~ | ❌ **RETRACTED** — same author, same machine, author-written prompt. Not independent. |
| 5 | ~~Empirical Hardware Tokens~~ | ~~Gemini 3.8 Flash: 21,643 active tokens saved (19.3%)~~ | ❌ **RETRACTED** — arms received different tasks; not attributable to the framework. n = 1. |

## What row 5 actually measured

The token arithmetic reproduces from two real transcripts. The comparison does
not: the governed arm's requirements named `AsyncMutex` and race conditions; the
free arm's did not. The difference is explained by the prompt. See
`docs/case-studies/GEMINI_N1.md`.

## Why this file was edited instead of deleted

Because "we removed the evidence" is indistinguishable from "the evidence
disappeared". Keeping the original claim visible next to its retraction is the
only version of this document that can be audited later.
