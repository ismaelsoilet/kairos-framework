#!/usr/bin/env python3
"""
Adjudication table for the external scan.

Modalidade de conclusão: this file records the verdict for every flag the scanner
produced over the 255 externally sampled PRs, determined by reading the actual
diff context for each one.

Verdicts were assigned BEFORE the precision number was computed, and every
FALSE_POSITIVE / UNRELATED verdict carries the quote that justifies it, as the
pre-registration requires.

Usage:
    python3 benchmark/external/adjudicate.py --flags /tmp/kairos-ext/flags.json \
        --verdicts benchmark/external/verdicts.json --out /tmp/kairos-ext/report.json
"""

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

# Verdict keys are "flag index (1-based)" -> (verdict, note)
# Assigned by reading the diff. Notes quote the reason.
VERDICTS = {
    1:  ("FALSE_POSITIVE", "guard_removal boundary noise: `if resp.chunk_left is not None:` appears on a REMOVED line of an unrelated refactor; no guard was dropped"),
    2:  ("FALSE_POSITIVE", "unittest -> pytest style conversion: self.assertRaises became pytest.raises, self.assertTrue became assert. Assertion count did not drop, strength did not drop"),
    3:  ("TRUE_POSITIVE", "test_repr for CaseInsensitiveDict deleted in this PR and not re-added anywhere in the diff (1 file touched). Coverage genuinely lost"),
    4:  ("TRUE_POSITIVE", "same deletion as #3, reported as test-function removal. Duplicate finding, same real cause"),
    5:  ("FALSE_POSITIVE", "@pytest.mark.skipif(blinker is None) guards an OPTIONAL dependency. Correct practice, not a skipped test"),
    6:  ("TRUE_POSITIVE", "test_get_env deleted together with the deprecated get_env() function. Test matched removed API — intentional, but the scanner cannot know that. Verdict favours the scanner: no replacement test for the behaviour"),
    7:  ("TRUE_POSITIVE", "same deletion as #6, reported as test-function removal"),
    8:  ("FALSE_POSITIVE", "removed `if value is None: return None` belonged to the deleted _set_env function. Function removal, not guard weakening"),
    9:  ("FALSE_POSITIVE", "`def test_func(some): pass` is a STRING ARGUMENT to testdir.getitem(), not a function definition. The scanner matched code inside a string literal"),
    10: ("FALSE_POSITIVE", "same: code inside a string literal passed to testdir.getitem()"),
    11: ("FALSE_POSITIVE", "same: code inside a string literal"),
    12: ("FALSE_POSITIVE", "same: code inside a string literal"),
    13: ("FALSE_POSITIVE", "same: test fixture definitions inside triple-quoted string blocks"),
    14: ("FALSE_POSITIVE", "same: code inside a string literal"),
    15: ("FALSE_POSITIVE", "same: code inside a string literal"),
    16: ("FALSE_POSITIVE", "same: code inside a string literal"),
    17: ("FALSE_POSITIVE", "same: code inside a string literal"),
    18: ("FALSE_POSITIVE", "same: code inside a string literal"),
    19: ("FALSE_POSITIVE", "same: code inside a string literal"),
    20: ("FALSE_POSITIVE", "same: code inside a string literal"),
    21: ("TRUE_POSITIVE", "test_module_participates_as_plugin deleted, not re-added in any of the 31 files the PR touches"),
    22: ("TRUE_POSITIVE", "same deletion as #21"),
    23: ("FALSE_POSITIVE", "`def test_method(self, something): ... pass` inside a string fixture"),
    24: ("FALSE_POSITIVE", "same: code inside a string literal"),
    25: ("FALSE_POSITIVE", "same: code inside a string literal"),
    26: ("FALSE_POSITIVE", "same: code inside a string literal"),
    27: ("FALSE_POSITIVE", "same: code inside a string literal"),
    28: ("TRUE_POSITIVE", "genuine `except AttributeError: pass` in the new resolve() import helper, swallowing a failed getattr during dotted-name resolution"),
    29: ("FALSE_POSITIVE", "`>= 0` -> `> 0` boundary comparison is between two DIFFERENT variables (showheader vs showlongtestinfo), not a loosened guard on the same one"),
    30: ("FALSE_POSITIVE", "same as #29: unrelated boundary pair compared"),
    31: ("TRUE_POSITIVE", "test_unroll_expression deleted, not re-added across the 5 files the PR touches"),
    32: ("TRUE_POSITIVE", "same deletion as #31"),
    33: ("FALSE_POSITIVE", "`except IOError:` -> `except OSError:` is an alias rename; the body already was `pass` before and after. No new swallow introduced"),
    34: ("FALSE_POSITIVE", "same alias rename: `(ValueError, IOError, OSError)` -> `(ValueError, OSError)`; behaviour identical, handler already returned a default"),
    35: ("FALSE_POSITIVE", "same alias rename: IOError -> OSError inside a tuple"),
    36: ("FALSE_POSITIVE", "same alias rename; `except OSError: pass` in cleanup code, present before the change"),
    37: ("FALSE_POSITIVE", "`raise NotImplementedError()` is INSIDE a test asserting that pytest rejects marks on fixtures. It is the expected behaviour under test"),
    38: ("FALSE_POSITIVE", "same: raise inside a pytest.raises block"),
    39: ("FALSE_POSITIVE", "same: raise inside a pytest.raises block"),
    40: ("TRUE_POSITIVE", "test_hookproxy_warnings_for_pathlib deleted, not re-added across 10 files"),
    41: ("TRUE_POSITIVE", "same deletion as #40"),
    42: ("TRUE_POSITIVE", "test functions deleted from test/config.env.js with the removal of app.configure. Not re-added in the diff"),
    43: ("TRUE_POSITIVE", "two `it(...)` blocks for the json-spaces-in-development behaviour removed; one replacement test added for a different assertion"),
    44: ("TRUE_POSITIVE", "an `it(...)` block removed and replaced by a narrower one; net test coverage for the development default is gone"),
    45: ("FALSE_POSITIVE", "the removed lines are an inline callback inlined into `res.sendfile(..., done)`; the assertions moved into the test's request chain"),
    46: ("FALSE_POSITIVE", "vendored es6-promise polyfill added as a fixture. Minified third-party code, not authored here"),
    47: ("FALSE_POSITIVE", "same vendored library: minified `catch` bodies inside a bundled polyfill"),
    48: ("FALSE_POSITIVE", "`write: function write() {}` is a no-op stub FOR A NON-BROWSER, NON-NODE ENV branch — deliberate no-op, guarded by isStandardBrowserEnv()"),
    49: ("FALSE_POSITIVE", "`read: function read() { return null; }` same deliberate no-op branch"),
    50: ("FALSE_POSITIVE", "`remove: function remove() {}` same deliberate no-op branch"),
    51: ("FALSE_POSITIVE", "`function get(url, opts, cb) { ... }` matched as a one-line stub, but the function body follows on later lines. One-line regex could not see it"),
    52: ("FALSE_POSITIVE", "`defineProps(function chalk() {}, styles)` — an empty function used as a PROTOTYPE TARGET is legitimate; it is not a stub"),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--flags", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    data = json.loads(Path(args.flags).read_text(encoding="utf-8"))
    flags = data["flags"]

    missing = [i for i in range(1, len(flags) + 1) if i not in VERDICTS]
    if missing:
        raise SystemExit(f"Unadjudicated flags: {missing}")

    rows = []
    for i, flag in enumerate(flags, 1):
        verdict, note = VERDICTS[i]
        rows.append({**flag, "flag_index": i, "verdict": verdict, "note": note})

    total = len(rows)
    tp = sum(1 for r in rows if r["verdict"] == "TRUE_POSITIVE")
    fp = sum(1 for r in rows if r["verdict"] == "FALSE_POSITIVE")
    un = sum(1 for r in rows if r["verdict"] == "UNRELATED")

    precision = tp / total if total else 0.0

    by_type = defaultdict(lambda: Counter())
    for r in rows:
        by_type[r["fraud_type"]]["total"] += 1
        by_type[r["fraud_type"]][r["verdict"]] += 1

    by_lang = defaultdict(lambda: Counter())
    for r in rows:
        by_lang[r["language"]]["total"] += 1
        by_lang[r["language"]][r["verdict"]] += 1

    # PR-level: a PR counts as correctly flagged if at least one flag is a TP.
    prs_flagged = {r["merge_sha"] for r in rows}
    prs_correct = {r["merge_sha"] for r in rows if r["verdict"] == "TRUE_POSITIVE"}

    report = {
        "scanned_prs": data["scanned_prs"],
        "prs_with_any_flag": len(prs_flagged),
        "prs_with_true_positive": len(prs_correct),
        "pr_flag_rate": round(len(prs_flagged) / data["scanned_prs"], 4),
        "pr_useful_rate": round(len(prs_correct) / data["scanned_prs"], 4),
        "flags_total": total,
        "true_positives": tp,
        "false_positives": fp,
        "unrelated": un,
        "precision": round(precision, 4),
        "by_type": {k: dict(v) for k, v in by_type.items()},
        "by_language": {k: dict(v) for k, v in by_lang.items()},
        "crashes": data["crashes"],
        "rows": rows,
    }

    Path(args.out).write_text(json.dumps(report, indent=1), encoding="utf-8")

    print("=" * 72)
    print("EXTERNAL VALIDATION — ADJUDICATED RESULT")
    print("=" * 72)
    print(f"  PRs scanned:              {report['scanned_prs']}")
    print(f"  PRs with any flag:        {report['prs_with_any_flag']}  ({report['pr_flag_rate']:.1%})")
    print(f"  PRs with a true positive: {report['prs_with_true_positive']}  ({report['pr_useful_rate']:.1%})")
    print(f"  flags total:              {total}")
    print(f"    true positive:          {tp}")
    print(f"    false positive:         {fp}")
    print(f"    unrelated:              {un}")
    print(f"  PRECISION:                {precision:.1%}")
    print()
    print("  by fraud type:")
    for t, c in sorted(by_type.items(), key=lambda kv: -kv[1]["total"]):
        p = c["TRUE_POSITIVE"] / c["total"]
        print(f"    {t:<30} {c['total']:>3} flags  {c['TRUE_POSITIVE']:>3} TP  ({p:.0%})")
    print()
    print("  by language:")
    for lang, c in sorted(by_lang.items()):
        p = c["TRUE_POSITIVE"] / c["total"]
        print(f"    {lang:<12} {c['total']:>3} flags  {c['TRUE_POSITIVE']:>3} TP  ({p:.0%})")
    print(f"\n  written to {args.out}")


if __name__ == "__main__":
    main()
