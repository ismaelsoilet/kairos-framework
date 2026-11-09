#!/usr/bin/env python3
"""
Extract real merged-PR diffs from cloned repositories, using the sampling rule
fixed in PREREGISTRATION_EXTERNAL.md — before any result was seen.

Rule, verbatim from the pre-registration:
  - merge commits from the default branch history, chronological
  - fixed stride = max(1, total_merges // 40)
  - diff = <merge>^1...<merge>
  - exclude: no-diff merges, automated bot merges, diffs > 5000 changed lines

Output: one JSON file with every sampled PR and its diff, plus a manifest of
what was excluded and why. Deterministic: same input, same output.

Usage:
    python3 benchmark/external/extract_prs.py --repos-dir /tmp/kairos-ext/repos \
        --out /tmp/kairos-ext/sample.json
"""

import argparse
import json
import re
import subprocess
from pathlib import Path

WAVE1 = [
    ("psf/requests", "Python"),
    ("pallets/flask", "Python"),
    ("pytest-dev/pytest", "Python"),
    ("expressjs/express", "JavaScript"),
    ("axios/axios", "JavaScript"),
    ("sindresorhus/got", "TypeScript"),
    ("chalk/chalk", "JavaScript"),
    ("psf/black", "Python"),
]

# Wave 2, declared AFTER wave 1 was complete and its results reported. Kept in a
# separate list on purpose: pooling it with wave 1 would let the sample grow in
# whichever direction looked better, which is the bias the pre-registration
# forbids. Wave 2 exists to test one hypothesis — that wave 1's sample was
# unusually disciplined — and is reported separately.
WAVE2 = [
    ("django/django", "Python"),
    ("pallets/click", "Python"),
    ("encode/httpx", "Python"),
    ("tiangolo/fastapi", "Python"),
]

REPOS = WAVE1

BOT_RE = re.compile(r"(dependabot|pre-commit-ci|renovate|github-actions|snyk-bot|mergify)",
                    re.IGNORECASE)
TARGET_PER_REPO = 40
MAX_DIFF_LINES = 5000


def git(args, cwd, binary=False):
    res = subprocess.run(["git"] + args, cwd=cwd, capture_output=True)
    if res.returncode != 0:
        return None
    return res.stdout if binary else res.stdout.decode("utf-8", errors="replace")


def default_branch(repo_dir):
    out = git(["symbolic-ref", "refs/remotes/origin/HEAD"], repo_dir)
    if out and out.strip():
        return out.strip().rsplit("/", 1)[-1]
    for candidate in ("main", "master", "develop"):
        if git(["rev-parse", "--verify", f"origin/{candidate}"], repo_dir):
            return candidate
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repos-dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--wave", choices=["1", "2"], default="1")
    args = ap.parse_args()

    repo_list = WAVE1 if args.wave == "1" else WAVE2
    repos_dir = Path(args.repos_dir)
    all_prs = []
    manifest = []

    for full_name, language in repo_list:
        local = repos_dir / full_name.replace("/", "_")
        if not local.is_dir():
            manifest.append({"repo": full_name, "status": "missing_clone"})
            continue

        branch = default_branch(local)
        if not branch:
            manifest.append({"repo": full_name, "status": "no_default_branch"})
            continue

        # Merge commits, oldest first, first-parent chain.
        log = git(["log", "--merges", "--first-parent", "--reverse",
                   "--format=%H|%s", f"origin/{branch}"], local)
        if not log:
            manifest.append({"repo": full_name, "status": "no_history"})
            continue

        merges = []
        for line in log.splitlines():
            if "|" not in line:
                continue
            sha, subject = line.split("|", 1)
            merges.append((sha.strip(), subject.strip()))

        total = len(merges)
        stride = max(1, total // TARGET_PER_REPO)
        picked = merges[::stride][:TARGET_PER_REPO]

        kept = 0
        excluded_no_diff = 0
        excluded_bot = 0
        excluded_too_big = 0

        for sha, subject in picked:
            if BOT_RE.search(subject):
                excluded_bot += 1
                continue

            diff = git(["diff", "--no-color", f"{sha}^1...{sha}"], local)
            if not diff or not diff.strip():
                excluded_no_diff += 1
                continue

            changed = sum(1 for l in diff.splitlines()
                          if (l.startswith("+") and not l.startswith("+++"))
                          or (l.startswith("-") and not l.startswith("---")))
            if changed > MAX_DIFF_LINES:
                excluded_too_big += 1
                continue

            all_prs.append({
                "repo": full_name,
                "language": language,
                "branch": branch,
                "merge_sha": sha,
                "subject": subject,
                "changed_lines": changed,
                "diff": diff,
            })
            kept += 1

        manifest.append({
            "repo": full_name,
            "status": "ok",
            "language": language,
            "branch": branch,
            "merges_available": total,
            "stride": stride,
            "picked": len(picked),
            "kept": kept,
            "excluded_bot": excluded_bot,
            "excluded_no_diff": excluded_no_diff,
            "excluded_too_big": excluded_too_big,
        })
        print(f"{full_name:<24} merges={total:>4} stride={stride:>3} "
              f"picked={len(picked):>3} kept={kept:>3} "
              f"(bot={excluded_bot} nodiff={excluded_no_diff} big={excluded_too_big})")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"manifest": manifest, "prs": all_prs}, indent=1),
                   encoding="utf-8")

    total_lines = sum(p["changed_lines"] for p in all_prs)
    print(f"\nTotal PRs: {len(all_prs)}  changed lines: {total_lines:,}")
    print(f"Written to {out}")


if __name__ == "__main__":
    main()
