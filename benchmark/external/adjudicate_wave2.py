#!/usr/bin/env python3
"""
Adjudication for wave 2 — repositories added AFTER wave 1 was complete and its
results reported. Kept separate on purpose: pooling would let the sample grow in
whichever direction flattered the tool.

Wave 2 was chosen to test one hypothesis: that wave 1's sample (mature projects
with strict review) was unusually disciplined, so the flag rate would be higher.

Usage:
    python3 benchmark/external/adjudicate_wave2.py --flags /tmp/kairos-ext/flags_w2.json
"""

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

V = {
    1:  ("FALSE_POSITIVE", "`except LookupError: pass` in a locale lookup — deliberate fallback chain, pre-existing"),
    2:  ("FALSE_POSITIVE", "guard was REWRITTEN into a variants loop, not removed; the new code validates four fallbacks instead of one"),
    3:  ("FALSE_POSITIVE", "`except LookupError: continue` inside a loop over candidate locales — retry, not swallow"),
    4:  ("FALSE_POSITIVE", "`except ImportError: pass` guarding an optional import — the canonical legitimate use"),
    5:  ("FALSE_POSITIVE", "same pattern: optional capability probe"),
    6:  ("FALSE_POSITIVE", "same pattern: optional import"),
    7:  ("FALSE_POSITIVE", "`def cmd(arg): pass` is a @click.command body inside a test; an empty click handler is the fixture under test"),
    8:  ("FALSE_POSITIVE", "same: click command body in a test fixture"),
    9:  ("FALSE_POSITIVE", "same: click command body in a test fixture"),
    10: ("FALSE_POSITIVE", "same: click command body in a test fixture"),
    11: ("FALSE_POSITIVE", "skipif(not WIN) — platform guard, correct practice"),
    12: ("FALSE_POSITIVE", "assertion count changed because a factory was replaced by a direct instance; assertions stayed as strong"),
    13: ("TRUE_POSITIVE", "21 assertions removed vs 1 added in tests/test_api.py across this PR"),
    14: ("FALSE_POSITIVE", "`if stream:` removed as part of a signature change; the guard's role moved to the caller"),
    15: ("FALSE_POSITIVE", "`raise NotImplementedError()  # pragma: nocover` in an abstract interface — that IS the implementation"),
    16: ("FALSE_POSITIVE", "same: abstract method in an interface"),
    17: ("FALSE_POSITIVE", "`except h11.ProtocolError: pass` — protocol-level recoverable error, deliberate"),
    18: ("FALSE_POSITIVE", "`except KeyError: return None` — lookup miss, documented behaviour"),
    19: ("FALSE_POSITIVE", "abstract interface method"),
    20: ("FALSE_POSITIVE", "abstract interface method"),
    21: ("TRUE_POSITIVE", "12 assertions removed from tests/test_responses.py with none added"),
    22: ("FALSE_POSITIVE", "`if max_connections is not None:` rewritten in the same diff, not dropped"),
    23: ("FALSE_POSITIVE", "`if hasattr(asyncio, 'run')` capability probe rewritten for a compat shim"),
    24: ("FALSE_POSITIVE", "abstract interface method"),
    25: ("FALSE_POSITIVE", "abstract interface method"),
    26: ("FALSE_POSITIVE", "abstract interface method"),
    27: ("FALSE_POSITIVE", "abstract interface method"),
    28: ("FALSE_POSITIVE", "abstract interface method"),
    29: ("FALSE_POSITIVE", "abstract interface method"),
    30: ("FALSE_POSITIVE", "abstract interface method"),
    31: ("FALSE_POSITIVE", "abstract interface method"),
    32: ("FALSE_POSITIVE", "abstract interface method"),
    33: ("TRUE_POSITIVE", "4 assertions removed vs 1 added in tests/test_config.py"),
    34: ("TRUE_POSITIVE", "3 test functions removed with no replacement in tests/test_config.py"),
    35: ("FALSE_POSITIVE", "`if not self.components.scheme:` rewritten, not removed"),
    36: ("FALSE_POSITIVE", "`except KeyError: return None` — lookup miss in a connection pool"),
    37: ("FALSE_POSITIVE", "recoverable protocol error, deliberate"),
    38: ("FALSE_POSITIVE", "redirect-limit guard rewritten alongside the surrounding logic"),
    39: ("TRUE_POSITIVE", "11 assertions removed from tests/test_sync.py with none added"),
    40: ("TRUE_POSITIVE", "5 test functions removed from tests/test_sync.py"),
    41: ("FALSE_POSITIVE", "brotli decode error handled with a logged fallback, marked nocover"),
    42: ("FALSE_POSITIVE", "abstract interface method"),
    43: ("FALSE_POSITIVE", "abstract interface method"),
    44: ("FALSE_POSITIVE", "abstract base method in httpx/concurrency/base.py"),
    45: ("FALSE_POSITIVE", "abstract base method"),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--flags", required=True)
    args = ap.parse_args()

    data = json.loads(Path(args.flags).read_text(encoding="utf-8"))
    flags = data["flags"]
    missing = [i for i in range(1, len(flags) + 1) if i not in V]
    if missing:
        raise SystemExit(f"Unadjudicated: {missing}")

    rows = [{"i": i, **fl, "verdict": V[i][0], "note": V[i][1]} for i, fl in enumerate(flags, 1)]
    tp = sum(1 for r in rows if r["verdict"] == "TRUE_POSITIVE")
    fp = len(rows) - tp

    by_type = defaultdict(Counter)
    for r in rows:
        by_type[r["fraud_type"]]["total"] += 1
        by_type[r["fraud_type"]][r["verdict"]] += 1

    prs = {r["merge_sha"] for r in rows}
    prs_tp = {r["merge_sha"] for r in rows if r["verdict"] == "TRUE_POSITIVE"}

    print("=" * 72)
    print("WAVE 2 — repos added after wave 1 was reported (never seen before)")
    print("=" * 72)
    print(f"  PRs scanned:                  {data['scanned_prs']}")
    print(f"  PRs with any flag:            {len(prs)}  ({len(prs)/data['scanned_prs']:.1%})")
    print(f"  PRs with a true positive:     {len(prs_tp)}  ({len(prs_tp)/data['scanned_prs']:.1%})")
    print(f"  flags:                        {len(rows)}")
    print(f"    true positive:              {tp}")
    print(f"    false positive:             {fp}")
    print(f"  PRECISION:                    {tp/len(rows):.1%}")
    print()
    print("  by fraud type:")
    for t, c in sorted(by_type.items(), key=lambda kv: -kv[1]["total"]):
        p = c.get("TRUE_POSITIVE", 0) / c["total"]
        print(f"    {t:<30} {c['total']:>3} flags  {c.get('TRUE_POSITIVE',0):>3} TP  ({p:.0%})")


if __name__ == "__main__":
    main()
