#!/usr/bin/env python3
"""
Brainstorm brief: force alternatives to exist before a spec is written.

Why this is separate from the spec: a spec commits to one design. If the
alternatives were never written down, the commit is not a decision, it is the
first idea that survived the conversation. The benchmark this project relies on
found spec quality predicts merge rate (89.3% vs 60.0% above six of eight items),
and one of those eight is scope — which is only meaningful if something was
excluded on purpose.

OpenSpec's `/opsx:explore` is a thinking stance, by design non-linear and with no
mandatory output. EGM's brainstorm produces a brief, which is the property worth
keeping: an artifact that can be reviewed, diffed, and checked.

This module scaffolds that artifact and checks it. It does not generate ideas; an
agent or a human writes them. A brief with three real alternatives and a stated
rejection reason each is worth more than a page of prose, and it is checkable.

What is checked:
  - at least MIN_ALTERNATIVES alternatives
  - each alternative has a rejection reason (or is the chosen one)
  - assumptions and open questions are present
  - a "what would make this wrong" section exists

Nothing here is a measurement. It is a structure that makes an unexamined
first idea visible as such.
"""

import re
from pathlib import Path

MIN_ALTERNATIVES = 3
BRIEF_NAME = "brainstorm.md"

REQUIRED_SECTIONS = [
    ("problem", [r"\bproblem", r"\bgoal", r"\bintent"]),
    ("alternatives", [r"\balternativ", r"\boptions?\b", r"\bapproaches?\b"]),
    ("chosen", [r"\bchosen\b", r"\bdecision\b", r"\bselected\b", r"\bwhy this"]),
    ("assumptions", [r"\bassumptions?\b", r"\bwhat we are assuming"]),
    ("open_questions", [r"\bopen questions?\b", r"\bunknowns?\b", r"\bunresolved"]),
    ("falsification", [r"\bwhat would make this wrong", r"\bdisconfirm", r"\bwould prove this wrong"]),
]


def _sections(text):
    out, current, body = {}, "_preamble", []
    for line in text.splitlines():
        if re.match(r"^#{1,3}\s+", line):
            out[current] = "\n".join(body)
            current, body = line.lstrip("# ").strip().lower(), []
        else:
            body.append(line)
    out[current] = "\n".join(body)
    return out


def parse_alternatives(text):
    """Extract alternatives and whether each carries a rejection reason.

    An alternative counts when it is a numbered or bulleted entry under an
    alternatives heading. It is 'resolved' when the entry says why it was
    rejected, or marks itself as the chosen one.
    """
    secs = _sections(text)
    alt_body = "\n".join(body for head, body in secs.items()
                         if any(re.search(p, head, re.I) for p in REQUIRED_SECTIONS[1][1]))
    if not alt_body.strip():
        return []

    entries, current = [], None
    for line in alt_body.splitlines():
        m = re.match(r"^\s*(?:\d+[.)]|[-*])\s+(.+)$", line)
        if m and not line.startswith(("  ", "\t")):
            current = {"title": m.group(1).strip(), "body": []}
            entries.append(current)
        elif current is not None:
            current["body"].append(line)

    out = []
    for e in entries:
        body = "\n".join(e["body"])
        has_reason = bool(re.search(
            r"\b(reject|rejected|ruled out|not chosen|discard|why not|"
            r"because|trade-?off|downside|chosen)\b", body, re.I))
        is_chosen = bool(re.search(r"\b(chosen|selected)\b", e["title"] + body, re.I))
        out.append({"title": e["title"][:120], "has_reason": has_reason,
                    "chosen": is_chosen})
    return out


def check_brief(text):
    """Return {ok, score, present, missing, alternatives, problems}."""
    secs = _sections(text)
    present, missing = [], []
    for name, patterns in REQUIRED_SECTIONS:
        hit = any(re.search(p, head, re.I) for head in secs for p in patterns)
        (present if hit else missing).append(name)

    alts = parse_alternatives(text)
    unresolved = [a for a in alts if not a["has_reason"] and not a["chosen"]]
    problems = []

    if len(alts) < MIN_ALTERNATIVES:
        problems.append(
            f"only {len(alts)} alternative(s); at least {MIN_ALTERNATIVES} are needed "
            f"to show this was a decision and not the first idea")
    if unresolved:
        problems.append(
            f"{len(unresolved)} alternative(s) have no rejection reason: "
            + "; ".join(a["title"][:50] for a in unresolved[:3]))
    if "falsification" in missing:
        problems.append(
            "no 'what would make this wrong' section — without it, no observation "
            "could change the decision")

    return {
        "ok": not problems,
        "sections_present": present,
        "sections_missing": missing,
        "alternatives": len(alts),
        "unresolved": len(unresolved),
        "problems": problems,
    }


TEMPLATE = """# Brainstorm: {name}

> Written **before** the spec. A spec commits to one design; this file records
> what was rejected and why, so the commit is a decision rather than the first
> idea that survived the conversation.

## Problem
<!-- One or two sentences. What is actually wrong today? -->

## Alternatives considered
<!-- At least three. Each one needs a reason it was not chosen. -->

1. **Alternative one**
   - Mechanism:
   - Why rejected:
2. **Alternative two**
   - Mechanism:
   - Why rejected:
3. **Alternative three**
   - Mechanism:
   - Why rejected:

## Chosen approach
<!-- Which one, and the trade-off you are accepting by choosing it. -->

## Assumptions
<!-- What has to be true for this to work, that you have not verified. -->

## Open questions
<!-- What you do not know yet. Each one should say how it gets answered. -->

## What would make this wrong
<!-- The observation that would force a rethink. Be specific enough that it
     could actually happen. "It doesn't work" is not an answer. -->

## Live versions checked
<!-- Run `kairos scout` and paste what it found for the packages involved. This
     is the one section that must come from a command, not from memory. -->
"""


def main():  # pragma: no cover - thin CLI wrapper
    import argparse
    ap = argparse.ArgumentParser(description="Brainstorm brief scaffold and check")
    ap.add_argument("--new", metavar="NAME", help="write a template brief")
    ap.add_argument("--check", metavar="PATH", help="check an existing brief")
    ap.add_argument("--out", default=None, help="output path for --new")
    args = ap.parse_args()

    if args.new:
        target = Path(args.out or BRIEF_NAME)
        if target.exists():
            print(f"exists, not overwriting: {target}")
            return 1
        target.write_text(TEMPLATE.format(name=args.new), encoding="utf-8")
        print(f"wrote {target}")
        print("Fill it in before running `kairos spec`. A blank brief is worse than none.")
        return 0

    if args.check:
        p = Path(args.check)
        if not p.is_file():
            print(f"not found: {p}")
            return 1
        result = check_brief(p.read_text(encoding="utf-8", errors="replace"))
        print("=" * 68)
        print(f"BRAINSTORM CHECK — {'OK' if result['ok'] else 'INCOMPLETE'}")
        print("=" * 68)
        print(f"  alternatives:     {result['alternatives']} (need {MIN_ALTERNATIVES})")
        print(f"  without reason:   {result['unresolved']}")
        print(f"  sections present: {', '.join(result['sections_present']) or 'none'}")
        if result["sections_missing"]:
            print(f"  sections missing: {', '.join(result['sections_missing'])}")
        if result["problems"]:
            print("  problems:")
            for p_ in result["problems"]:
                print(f"    - {p_}")
        print("=" * 68)
        return 0 if result["ok"] else 1

    print("Nothing to do. Use --new NAME or --check PATH.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
