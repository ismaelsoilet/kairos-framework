#!/usr/bin/env python3
"""
Run the scanner over the externally sampled PR diffs and emit every flag for
adjudication.

Nothing is filtered here. Every violation the scanner produces is written to
the output, including duplicates, because the adjudication step needs to see
what was actually matched.

Usage:
    python3 benchmark/external/scan_prs.py --sample /tmp/kairos-ext/sample.json \
        --out /tmp/kairos-ext/flags.json
"""

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from kairos_cli import scan_diff_text  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    sample = json.loads(Path(args.sample).read_text(encoding="utf-8"))
    prs = sample["prs"]

    flags = []
    per_type = {}
    per_language = {}
    prs_with_flags = 0
    crashed = []

    for pr in prs:
        lang = pr["language"]
        per_language.setdefault(lang, {"prs": 0, "flagged": 0})
        per_language[lang]["prs"] += 1

        try:
            violations = scan_diff_text(pr["diff"])
        except Exception as exc:  # a crash is a finding, not a reason to skip
            crashed.append({"repo": pr["repo"], "sha": pr["merge_sha"],
                            "error": f"{type(exc).__name__}: {exc}"})
            continue

        if violations:
            prs_with_flags += 1
            per_language[lang]["flagged"] += 1

        for v in violations:
            per_type[v["fraud_type"]] = per_type.get(v["fraud_type"], 0) + 1
            flags.append({
                "repo": pr["repo"],
                "language": lang,
                "merge_sha": pr["merge_sha"],
                "subject": pr["subject"],
                "file": v["file"],
                "line": v["line"],
                "fraud_type": v["fraud_type"],
                "description": v["description"],
            })

    total = len(prs)
    result = {
        "scanned_prs": total,
        "prs_with_at_least_one_flag": prs_with_flags,
        "pr_flag_rate": round(prs_with_flags / total, 4) if total else 0,
        "flags_total": len(flags),
        "flags_by_type": per_type,
        "by_language": per_language,
        "crashes": crashed,
        "flags": flags,
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=1), encoding="utf-8")

    print("=" * 70)
    print("EXTERNAL SCAN — RAW OUTPUT (before adjudication)")
    print("=" * 70)
    print(f"  PRs scanned:            {total}")
    print(f"  PRs with >=1 flag:      {prs_with_flags}  "
          f"({prs_with_flags / total:.1%})" if total else "")
    print(f"  total flags:            {len(flags)}")
    print(f"  scanner crashes:        {len(crashed)}")
    print("\n  flags by type:")
    for t, n in sorted(per_type.items(), key=lambda kv: -kv[1]):
        print(f"    {t:<32} {n}")
    print("\n  by language:")
    for lang, st in sorted(per_language.items()):
        rate = st["flagged"] / st["prs"] if st["prs"] else 0
        print(f"    {lang:<12} prs={st['prs']:>3}  flagged={st['flagged']:>3}  ({rate:.0%})")
    print(f"\n  written to {out}")


if __name__ == "__main__":
    main()
