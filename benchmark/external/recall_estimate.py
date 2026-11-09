#!/usr/bin/env python3
"""
R1 — test-deletion recall estimate.

Independent of the scanner: find PRs whose diff mechanically removes assertion
lines or test functions from test files, then check whether the scanner flagged
the same PR. This measures whether the scanner catches the one fraud class that
is objectively detectable by diff arithmetic.

Pre-registered as an ESTIMATE of recall, never as measured recall.

Usage:
    python3 benchmark/external/recall_estimate.py --sample /tmp/kairos-ext/sample.json \
        --flags /tmp/kairos-ext/flags.json
"""

import argparse
import json
import re
from pathlib import Path

ASSERT_RE = re.compile(r"^\s*(await\s+)?(assert\b|self\.assert\w+|expect\(|\.should\b)")
TESTFN_RE = re.compile(r"^\s*(def\s+test_\w+|it\s*\(|test\s*\()")


def is_test_path(path):
    p = path.lower()
    parts = p.split("/")
    if any(x in ("tests", "test", "__tests__", "spec", "specs") for x in parts[:-1]):
        return True
    f = parts[-1]
    return (f.startswith("test_") or f.endswith("_test.py") or f.endswith(".test.js")
            or f.endswith(".spec.js") or f.endswith(".test.ts") or f.endswith(".spec.ts")
            or f.endswith(".test.jsx") or f.endswith(".test.tsx"))


def mechanical_findings(diff):
    """Files where a test file lost assertions or test functions, by arithmetic only."""
    cur = None
    stats = {}
    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            cur = line[6:].strip()
            stats.setdefault(cur, {"assert_del": 0, "assert_add": 0,
                                   "test_del": 0, "test_add": 0})
            continue
        if line.startswith("+++ /dev/null"):
            cur = None
            continue
        if not cur or not is_test_path(cur):
            continue
        if line.startswith("+") and not line.startswith("+++"):
            body = line[1:]
            if ASSERT_RE.match(body):
                stats[cur]["assert_add"] += 1
            if TESTFN_RE.match(body):
                stats[cur]["test_add"] += 1
        elif line.startswith("-") and not line.startswith("---"):
            body = line[1:]
            if ASSERT_RE.match(body):
                stats[cur]["assert_del"] += 1
            if TESTFN_RE.match(body):
                stats[cur]["test_del"] += 1

    findings = []
    for path, s in stats.items():
        if s["assert_del"] > s["assert_add"]:
            findings.append((path, "assert_net_loss", s["assert_del"] - s["assert_add"]))
        if s["test_del"] > s["test_add"]:
            findings.append((path, "testfn_net_loss", s["test_del"] - s["test_add"]))
    return findings


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", required=True)
    ap.add_argument("--flags", required=True)
    args = ap.parse_args()

    sample = json.loads(Path(args.sample).read_text(encoding="utf-8"))
    flagged_prs = {f["merge_sha"] for f in json.loads(
        Path(args.flags).read_text(encoding="utf-8"))["flags"]}

    detected = 0
    missed = []
    total = 0

    for pr in sample["prs"]:
        findings = mechanical_findings(pr["diff"])
        if not findings:
            continue
        total += 1
        if pr["merge_sha"] in flagged_prs:
            detected += 1
        else:
            missed.append({
                "repo": pr["repo"],
                "sha": pr["merge_sha"],
                "subject": pr["subject"][:70],
                "findings": findings[:3],
            })

    rate = detected / total if total else 0
    print("=" * 72)
    print("R1 — TEST-DELETION RECALL (ESTIMATE, NOT MEASURED RECALL)")
    print("=" * 72)
    print(f"  PRs with mechanical test/assert loss: {total}")
    print(f"  of those, flagged by the scanner:     {detected}")
    print(f"  detected rate:                        {rate:.1%}")
    print()
    if missed:
        print("  NOT flagged (false negatives):")
        for m in missed[:12]:
            print(f"    {m['repo']:<22} {m['subject']}")
            for f in m["findings"]:
                print(f"        {f[1]} in {f[0]} (-{f[2]})")
    print()


if __name__ == "__main__":
    main()
