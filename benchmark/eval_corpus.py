#!/usr/bin/env python3
"""
Fraud corpus evaluation: measures scanner recall and precision against a
labelled set of diffs whose expected verdicts were written before the scanner
was changed.

Definitions:
  recall    = caught frauds / total frauds
  precision = correctly-flagged frauds / everything flagged
              (a clean diff that is flagged counts as a false positive)

Usage:
    python3 benchmark/eval_corpus.py [--verbose] [--json]

Exit code 0 when the measured numbers meet the floors declared in
benchmark/PREREGISTRATION.md, 1 otherwise. The floors are a gate, not a
result: the printed numbers are whatever they are.
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from kairos_cli import scan_diff_text, DEFAULT_OFF_RULES  # noqa: E402

CORPUS = REPO_ROOT / "tests" / "fixtures" / "fraud_corpus" / "corpus.json"

RECALL_FLOOR = 0.90
PRECISION_FLOOR = 0.90

# The corpus measures the full detector, so every rule is enabled here. Default-off
# rules are still implemented and still covered — they are simply not on by default
# because external precision was 0% (see docs/EXTERNAL_VALIDATION.md).
ALL_RULES = tuple(DEFAULT_OFF_RULES)


def evaluate(verbose=False):
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    cases = corpus["cases"]

    fraud_cases = [c for c in cases if c["expected"] == "caught"]
    clean_cases = [c for c in cases if c["expected"] == "clean"]

    true_positives = 0
    false_negatives = []
    false_positives = []
    wrong_type = []

    for case in fraud_cases:
        violations = scan_diff_text(case["diff"], enable_rules=ALL_RULES)
        hit = bool(violations)
        if hit:
            true_positives += 1
            types = {v["fraud_type"] for v in violations}
            if case.get("expected_fraud_type") and case["expected_fraud_type"] not in types:
                wrong_type.append({
                    "id": case["id"],
                    "expected": case["expected_fraud_type"],
                    "got": sorted(types),
                })
        else:
            false_negatives.append(case)
        if verbose:
            mark = "caught" if hit else "MISS  "
            print(f"  [{mark}] {case['id']:<40} expected={case['expected_fraud_type']}")

    for case in clean_cases:
        violations = scan_diff_text(case["diff"], enable_rules=ALL_RULES)
        if violations:
            false_positives.append({
                "id": case["id"],
                "violations": [v["fraud_type"] for v in violations],
            })
        if verbose:
            mark = "FP    " if violations else "clean "
            print(f"  [{mark}] {case['id']:<40} expected=clean")

    total_flagged = true_positives + len(false_positives)
    recall = true_positives / len(fraud_cases) if fraud_cases else 0.0
    precision = true_positives / total_flagged if total_flagged else 0.0

    return {
        "cases_total": len(cases),
        "fraud_cases": len(fraud_cases),
        "clean_cases": len(clean_cases),
        "true_positives": true_positives,
        "false_negatives": [c["id"] for c in false_negatives],
        "false_positives": false_positives,
        "wrong_type": wrong_type,
        "recall": round(recall, 4),
        "precision": round(precision, 4),
        "recall_floor": RECALL_FLOOR,
        "precision_floor": PRECISION_FLOOR,
        "passes_gate": recall >= RECALL_FLOOR and precision >= PRECISION_FLOOR,
    }


def main(argv):
    verbose = "--verbose" in argv
    as_json = "--json" in argv

    result = evaluate(verbose=verbose)

    if as_json:
        print(json.dumps(result, indent=2))
    else:
        print("=" * 66)
        print("FRAUD CORPUS EVALUATION")
        print("=" * 66)
        print(f"  cases:            {result['cases_total']} "
              f"({result['fraud_cases']} fraud, {result['clean_cases']} clean)")
        print(f"  true positives:   {result['true_positives']}")
        print(f"  false negatives:  {len(result['false_negatives'])}")
        for cid in result["false_negatives"]:
            print(f"      - {cid}")
        print(f"  false positives:  {len(result['false_positives'])}")
        for fp in result["false_positives"]:
            print(f"      - {fp['id']} -> {fp['violations']}")
        if result["wrong_type"]:
            print(f"  right verdict, wrong fraud_type: {len(result['wrong_type'])}")
            for wt in result["wrong_type"]:
                print(f"      - {wt['id']}: expected {wt['expected']}, got {wt['got']}")
        print(f"  recall:           {result['recall']:.1%}  (floor {result['recall_floor']:.0%})")
        print(f"  precision:        {result['precision']:.1%}  (floor {result['precision_floor']:.0%})")
        print(f"  gate:             {'PASS' if result['passes_gate'] else 'FAIL'}")
        print("=" * 66)

    return 0 if result["passes_gate"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
