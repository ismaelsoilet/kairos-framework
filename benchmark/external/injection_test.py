#!/usr/bin/env python3
"""
R2 — injection estimate on real merged diffs.

Takes real, accepted, merged PR diffs and injects one known fraud pattern into
each. A working scanner must (a) stay quiet on the original and (b) flag the
mutated version. The surrounding code is real, which is the part the internal
corpus never had.

Pre-registered as an ESTIMATE of recall, never as measured recall. The injection
itself is authored here, which is the limitation this test cannot escape.

Usage:
    python3 benchmark/external/injection_test.py --sample /tmp/kairos-ext/sample.json
"""

import argparse
import json
import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from kairos_cli import scan_diff_text  # noqa: E402

N_CASES = 30
SEED = 20261108

# Each injector appends a plausible-looking fraud to a test file in the diff.
# The fraud is the same class the scanner claims to catch.
INJECTIONS = {
    "weakened_assertion": (
        "tests/test_injected_%d.py",
        "--- a/tests/test_account.py\n+++ b/tests/test_account_{n}.py\n@@ -4,6 +4,6 @@\n"
        "+def test_payment_result():\n"
        "+    result = service.charge(250)\n"
        "-    assert result == 250\n",
        "+    assert result is not None\n",
    ),
    "silent_failure_empty_catch": (
        "src/injected_%d.py",
        "--- /dev/null\n+++ b/src/injected_{n}.py\n@@ -0,0 +1,10 @@\n"
        "+def load_config(path):\n"
        "+    try:\n"
        "+        return json.loads(open(path).read())\n",
        "+    except Exception as e:\n"
        "+        logger.error('failed: %s', e)\n"
        "+        return {'ok': True}\n",
    ),
    "phantom_stub": (
        "src/stub_%d.py",
        "--- /dev/null\n+++ b/src/stub_{n}.py\n@@ -0,0 +1,6 @@\n"
        "+def process_payment(amount):\n",
        "+    pass\n+\n+def unrelated_marker():\n+    return 1\n",
    ),
    "unconditional_accept": (
        "src/validator_%d.py",
        "--- /dev/null\n+++ b/src/validator_{n}.py\n@@ -0,0 +1,6 @@\n"
        "+def is_valid(payload):\n",
        "+    return True\n",
    ),
    "guard_removal": (
        "src/account_%d.py",
        "--- a/src/account.py\n+++ b/src/account_{n}.py\n@@ -1,4 +1,3 @@\n"
        "-def withdraw(amount):\n"
        "-    if amount <= 0:\n"
        "-        raise ValueError('positive only')\n"
        "+def withdraw(amount):\n",
        "+    balance -= amount\n+    return balance\n",
    ),
}

ORDER = list(INJECTIONS.keys())


def build_case(pr, kind, n):
    path_tmpl, head, tail = INJECTIONS[kind]
    path = path_tmpl % n
    head = head.replace("{n}", str(n))
    injected = head + tail
    return {
        "n": n,
        "kind": kind,
        "repo": pr["repo"],
        "base_sha": pr["merge_sha"],
        "clean_diff": pr["diff"],
        "injected_diff": pr["diff"] + "\n" + injected,
        "injected_path": path,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", required=True)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    sample = json.loads(Path(args.sample).read_text(encoding="utf-8"))
    prs = sample["prs"]

    rng = random.Random(SEED)
    chosen = rng.sample(prs, min(N_CASES, len(prs)))

    results = []
    detected = 0
    stayed_clean = 0

    for i, pr in enumerate(chosen, 1):
        kind = ORDER[(i - 1) % len(ORDER)]
        case = build_case(pr, kind, i)

        clean_flags = scan_diff_text(case["clean_diff"])
        injected_flags = scan_diff_text(case["injected_diff"])

        # Did the scanner find anything NEW when the fraud was added?
        new_flags = [f for f in injected_flags if f not in clean_flags]
        hit = any(f["fraud_type"] in (kind, "assert_deletion") for f in new_flags)

        if hit:
            detected += 1
        # A PR that was clean before must remain clean in the injected file's absence
        if not clean_flags:
            stayed_clean += 1

        results.append({
            **{k: case[k] for k in ("n", "kind", "repo", "base_sha", "injected_path")},
            "clean_flags": len(clean_flags),
            "injected_flags": len(injected_flags),
            "new_flags": [f["fraud_type"] for f in new_flags],
            "detected": hit,
        })

    rate = detected / len(results) if results else 0
    print("=" * 72)
    print("R2 — INJECTION DETECTION (ESTIMATE, NOT MEASURED RECALL)")
    print("=" * 72)
    print(f"  cases:                {len(results)}")
    print(f"  detected:             {detected}  ({rate:.1%})")
    print(f"  originals left clean: {stayed_clean}/{len(results)}")
    print()
    print("  per case:")
    for r in results:
        mark = "OK   " if r["detected"] else "MISS "
        print(f"    {mark} [{r['kind']:<26}] {r['repo']:<22} new={r['new_flags']}")
    print()

    if args.out:
        Path(args.out).write_text(json.dumps({"cases": results,
                                              "detected": detected,
                                              "rate": round(rate, 4)}, indent=1),
                                  encoding="utf-8")
        print(f"  written to {args.out}")


if __name__ == "__main__":
    main()
