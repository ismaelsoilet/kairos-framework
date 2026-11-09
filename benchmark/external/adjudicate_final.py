#!/usr/bin/env python3
"""
Final adjudication for the external scan.

This version corresponds to flags5.json — the output AFTER the fixes driven by
this study (string-literal context tracking, statement-anchored function stubs,
inline-block handling). The earlier adjudication on flags.json is preserved in
EXTERNAL_VALIDATION.md as the "before" measurement.

Ordering principle, as pre-registered: when a flag is genuinely arguable, it is
recorded as FALSE_POSITIVE. The scanner is assumed wrong when uncertain.

Usage:
    python3 benchmark/external/adjudicate_final.py --flags /tmp/kairos-ext/flags5.json
"""

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

VERDICTS = {
    1:  ("FALSE_POSITIVE", "`if resp.chunk_left is not None:` sits on a removed line of an unrelated refactor; no guard was dropped"),
    2:  ("FALSE_POSITIVE", "unittest -> pytest style conversion (self.assertRaises -> pytest.raises). Assertion strength unchanged"),
    3:  ("TRUE_POSITIVE", "test_repr for CaseInsensitiveDict deleted, not re-added; PR touches 1 file"),
    4:  ("TRUE_POSITIVE", "same deletion, reported as test-function removal"),
    5:  ("FALSE_POSITIVE", "skipif on an optional dependency (blinker). Correct practice"),
    6:  ("TRUE_POSITIVE", "test_get_env deleted with the deprecated API. Intentional, but no replacement test for the behaviour"),
    7:  ("TRUE_POSITIVE", "same deletion as #6"),
    8:  ("FALSE_POSITIVE", "removed `if value is None: return None` belonged to the deleted _set_env function"),
    9:  ("TRUE_POSITIVE", "test_module_participates_as_plugin deleted, not re-added across 31 files"),
    10: ("TRUE_POSITIVE", "same deletion as #9"),
    11: ("TRUE_POSITIVE", "genuine `except AttributeError: pass` swallowing a failed getattr in the new resolve() helper"),
    12: ("FALSE_POSITIVE", "`>= 0` -> `> 0` compares two DIFFERENT variables (showheader vs showlongtestinfo)"),
    13: ("FALSE_POSITIVE", "same as #12"),
    14: ("TRUE_POSITIVE", "test_unroll_expression deleted, not re-added across 5 files"),
    15: ("TRUE_POSITIVE", "same deletion as #14"),
    16: ("FALSE_POSITIVE", "IOError -> OSError alias rename; handler body already was `pass`"),
    17: ("FALSE_POSITIVE", "same alias rename"),
    18: ("FALSE_POSITIVE", "same alias rename inside a tuple"),
    19: ("FALSE_POSITIVE", "same alias rename in cleanup code"),
    20: ("FALSE_POSITIVE", "`raise NotImplementedError()` inside a pytest.raises block; that IS the expected behaviour under test"),
    21: ("FALSE_POSITIVE", "same: raise inside pytest.raises"),
    22: ("FALSE_POSITIVE", "same: raise inside pytest.raises"),
    23: ("TRUE_POSITIVE", "test_hookproxy_warnings_for_pathlib deleted, not re-added across 10 files"),
    24: ("TRUE_POSITIVE", "same deletion as #23"),
    25: ("TRUE_POSITIVE", "test functions deleted with app.configure removal; not re-added"),
    26: ("TRUE_POSITIVE", "json-spaces development behaviour no longer covered; one narrower replacement test added"),
    27: ("TRUE_POSITIVE", "same as #26"),
    28: ("FALSE_POSITIVE", "callback inlined into res.sendfile(..., done); assertions moved into the request chain"),
    29: ("FALSE_POSITIVE", "vendored es6-promise polyfill. Minified third-party code, not authored in this PR"),
    30: ("FALSE_POSITIVE", "fragment view: the diff adds `function get(...) {` and `}` with the body outside the hunk. The scanner judges the diff, and the diff looks empty — a structural limit of diff-only analysis, not a rule that can be tightened"),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--flags", required=True)
    args = ap.parse_args()

    data = json.loads(Path(args.flags).read_text(encoding="utf-8"))
    flags = data["flags"]
    missing = [i for i in range(1, len(flags) + 1) if i not in VERDICTS]
    if missing:
        raise SystemExit(f"Unadjudicated flags: {missing}")

    rows = [{"flag_index": i, **flag, "verdict": VERDICTS[i][0], "note": VERDICTS[i][1]}
            for i, flag in enumerate(flags, 1)]

    total = len(rows)
    tp = sum(1 for r in rows if r["verdict"] == "TRUE_POSITIVE")
    fp = sum(1 for r in rows if r["verdict"] == "FALSE_POSITIVE")

    by_type = defaultdict(Counter)
    by_lang = defaultdict(Counter)
    for r in rows:
        by_type[r["fraud_type"]]["total"] += 1
        by_type[r["fraud_type"]][r["verdict"]] += 1
        by_lang[r["language"]]["total"] += 1
        by_lang[r["language"]][r["verdict"]] += 1

    prs_flagged = {r["merge_sha"] for r in rows}
    prs_correct = {r["merge_sha"] for r in rows if r["verdict"] == "TRUE_POSITIVE"}

    print("=" * 72)
    print("EXTERNAL VALIDATION — FINAL (after the fixes this study produced)")
    print("=" * 72)
    print(f"  PRs scanned:                  {data['scanned_prs']}")
    print(f"  PRs with any flag:            {len(prs_flagged)}  ({len(prs_flagged)/data['scanned_prs']:.1%})")
    print(f"  PRs with a true positive:     {len(prs_correct)}  ({len(prs_correct)/data['scanned_prs']:.1%})")
    print(f"  flags:                        {total}")
    print(f"    true positive:              {tp}")
    print(f"    false positive:             {fp}")
    print(f"  PRECISION:                    {tp/total:.1%}")
    print()
    print("  by fraud type:")
    for t, c in sorted(by_type.items(), key=lambda kv: -kv[1]["total"]):
        print(f"    {t:<28} {c['total']:>3} flags  {c.get('TRUE_POSITIVE',0):>3} TP  "
              f"({c.get('TRUE_POSITIVE',0)/c['total']:.0%})")
    print()
    print("  by language:")
    for lang, c in sorted(by_lang.items()):
        print(f"    {lang:<12} {c['total']:>3} flags  {c.get('TRUE_POSITIVE',0):>3} TP  "
              f"({c.get('TRUE_POSITIVE',0)/c['total']:.0%})")


if __name__ == "__main__":
    main()
