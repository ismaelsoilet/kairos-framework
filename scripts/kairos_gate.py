#!/usr/bin/env python3
"""
KAIROS gate: verify a delivered change against its specification.

Design comes from published evidence, not preference:

- Uvik SDD Benchmark 2026 (50 production Python tickets, blind review, control arm):
  spec frameworks merged 80-84%, control 72%; the noise band is ±10pp, so no
  framework beat another. What did separate outcomes:
    * specs covering >=6 of 8 checklist items merged 89.3% vs 60.0%
    * 7.9% of merged spec-arm tickets did NOT match their own spec (drift)
    * a spec paid back only on tickets touching >=3 files; on bug-fix, refactor
      and test-writing tickets the gain was 0pp while cost was higher
- METR RCT 2025: experienced developers were 19% SLOWER with AI while believing
  they were 20% faster. Self-report is not evidence.

Therefore this module does not generate specs and does not write code. It checks
the two things nobody checks: whether the spec was complete enough to be worth
following, and whether the delivered diff actually followed it.

Spec formats: KAIROS's own, or EGM (docs/designs/*.md), OpenSpec
(openspec/changes/*), or Spec Kit (specs/*/spec.md) — the section names are
matched loosely on purpose.
"""

import json
import re
from pathlib import Path

# Matched against heading TEXT (already stripped of the '#' markers), not the raw
# line, so these are plain substring patterns on the heading name.
CHECKLIST = [
    ("goal",              [r"\bgoal", r"\bproblem\b", r"\bobjective", r"\bintent\b"]),
    ("scope",             [r"\bscope\b", r"\bnon-?goals?\b"]),
    ("inputs_outputs",    [r"\binputs?\b", r"\boutputs?\b", r"\binterfaces?\b", r"\bapi\b", r"\bcontract"]),
    ("data_changes",      [r"\bdata\b", r"\bschemas?\b", r"\bmigrations?\b", r"\bmodels?\b", r"\bpayload"]),
    ("edge_cases",        [r"\bedge cases?\b", r"\berror", r"\bfailure", r"\bexception"]),
    ("acceptance_tests",  [r"\bacceptance\b", r"\btests?\b", r"\bverification\b", r"\bhow to (check|verify|prove)\b", r"\bvalidation\b"]),
    ("constraints",       [r"\bconstraints?\b", r"\bperformance\b", r"\bsecurity\b", r"\bcompatib", r"\blimits?\b"]),
    ("no_change_list",    [r"\bno[- ]change", r"\bmust not change\b", r"\binvariants?\b", r"\bnon-?goals?\b"]),
]

# 6 of 8 is the measured threshold (89.3% vs 60.0% merge rate).
COMPLETENESS_THRESHOLD = 6

# Files that plausibly count as "the change touched 3+ files" territory. Used only
# to warn that a spec may be overkill, never to block.
FIT_STATEMENTS = [
    "touches 3 or more files",
    "has 4 or more acceptance criteria",
    "crosses a module, service or repository boundary",
    "alters a data schema or a public API",
    "more than one engineer or agent will work on it",
    "the code is regulated or audited",
]
FIT_THRESHOLD = 3


class Spec:
    """Parsed specification: sections, criteria, declared scope, no-change list."""

    def __init__(self, path, text):
        self.path = Path(path)
        self.text = text
        self.sections = self._split_sections()
        self.criteria = self._extract_criteria()
        self.no_change = self._extract_no_change()
        self.declared_files = self._extract_files()

    def _split_sections(self):
        sections, current, body = {}, "_preamble", []
        for line in self.text.splitlines():
            if re.match(r"^#{1,3}\s+", line):
                sections[current] = "\n".join(body)
                current, body = line.lstrip("# ").strip().lower(), []
            else:
                body.append(line)
        sections[current] = "\n".join(body)
        return sections

    def completeness(self):
        """Return (score, present, missing) against the 8 measured items."""
        present, missing = [], []
        headings = [h for h in self.sections if h != "_preamble"]
        for name, patterns in CHECKLIST:
            hit = any(re.search(pat, h, re.IGNORECASE | re.MULTILINE)
                      for h in headings for pat in patterns)
            (present if hit else missing).append(name)
        return len(present), present, missing

    def _extract_criteria(self):
        """Checkbox or bullet items under an acceptance/verification section."""
        out = []
        for heading, body in self.sections.items():
            if not re.search(r"acceptance|verification|how to (check|verify|prove)|tests?", heading, re.IGNORECASE):
                continue
            for line in body.splitlines():
                m = re.match(r"^\s*[-*]\s*\[[ xX]?\]\s*(.+)$", line) or re.match(r"^\s*[-*]\s+(.+)$", line)
                if m:
                    text = m.group(1).strip()
                    if len(text) > 8:
                        out.append(text)
        return out

    def _extract_no_change(self):
        """Files or globs declared as must-not-change.

        Only backticked tokens that look like a path are taken. An earlier version
        also matched bare words, so the prose "the `gate` command must not break"
        became a rule that blocked any diff touching a file with "gate" in its
        name — the check accused the work it was meant to verify.
        """
        out = []
        for heading, body in self.sections.items():
            if not re.search(r"no[- ]change|must not change|invariant", heading, re.IGNORECASE):
                continue
            for m in re.finditer(r"`([^`]+)`", body):
                token = m.group(1).strip()
                if not token or token.startswith("http"):
                    continue
                # A path has a separator and a dot, or ends in a glob.
                if re.search(r"[/*]", token) and ("." in token or "*" in token):
                    out.append(token)
        return out

    def _extract_files(self):
        """Files the spec says it will touch (implementation plan / scope)."""
        out = set()
        for heading, body in self.sections.items():
            if not re.search(r"implementation|technical plan|files?|scope|design", heading, re.IGNORECASE):
                continue
            for m in re.finditer(r"`([\w./-]+\.\w{1,6})`", body):
                out.add(m.group(1).strip())
        return out


def parse_spec(path):
    """Parse a spec in any of the four layouts KAIROS claims to support.

    OpenSpec is different enough to need its own adapter: it is organised as
    capability deltas (`## ADDED Requirements` / `### Requirement:` /
    `#### Scenario:`), not as an implementation plan. Mapping it onto the same
    8-item checklist would score it 0/8 and wrongly call it weak — the format is
    simply answering different questions.
    """
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"spec not found: {p}")
    text = p.read_text(encoding="utf-8", errors="replace")
    if re.search(r"^##\s+(ADDED|MODIFIED|REMOVED|RENAMED)\b", text, re.MULTILINE):
        return OpenSpec(path, text)
    return Spec(path, text)


class OpenSpec(Spec):
    """A spec in OpenSpec delta format, adapted to the same gate contract.

    OpenSpec puts different things in different files:
      proposal.md  -> why (goal) and what changes (scope)
      specs/**.md  -> Requirement: blocks, each with Scenario: blocks
      design.md    -> technical decisions and the files to touch
      tasks.md     -> the implementation checklist

    The gate reads whatever of those exist next to the file it was pointed at.
    """

    def __init__(self, path, text):
        self.path = Path(path)
        self.text = text
        self.requirements = self._parse_requirements(text)
        change_dir = self.path.parent
        # Walk up to the change folder (the one holding proposal.md / tasks.md).
        for _ in range(4):
            if (change_dir / "proposal.md").exists() or (change_dir / "tasks.md").exists():
                break
            if change_dir.parent == change_dir:
                break
            change_dir = change_dir.parent
        self.change_dir = change_dir
        self.proposal = self._read(change_dir / "proposal.md")
        self.tasks = self._read(change_dir / "tasks.md")
        self.design = self._read(change_dir / "design.md")
        self.sections = {"_openspec": text}
        self.criteria = [f"{r['name']}: {r['scenario']}" if r['scenario'] else r['name']
                         for r in self.requirements if r["op"] in ("ADDED", "MODIFIED")]
        self.no_change = self._extract_no_change_openspec()
        self.declared_files = self._extract_files_openspec()

    @staticmethod
    def _read(p):
        return p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""

    def _parse_requirements(self, text):
        out, op, current = [], None, None
        for line in text.splitlines():
            m_op = re.match(r"^##\s+(ADDED|MODIFIED|REMOVED|RENAMED)\b", line)
            if m_op:
                op, current = m_op.group(1), None
                continue
            m_req = re.match(r"^###\s*Requirement:\s*(.+)$", line, re.IGNORECASE)
            if m_req:
                current = {"op": op, "name": m_req.group(1).strip(), "scenario": None}
                out.append(current)
                continue
            m_sc = re.match(r"^####\s*Scenario:\s*(.+)$", line, re.IGNORECASE)
            if m_sc and current is not None and current["scenario"] is None:
                current["scenario"] = m_sc.group(1).strip()
        return out

    def completeness(self):
        """OpenSpec vocabulary, scored against the same eight ideas.

        Goal comes from proposal "Why", scope from proposal "What changes",
        acceptance from Scenario blocks, constraints from design, edge cases from
        scenarios that describe failure. Items OpenSpec genuinely does not carry
        (data changes, no-change list) count as missing and are reported, not
        silently waved through.
        """
        present, missing = [], []
        haystack = " ".join([
            self.proposal, self.design, self.text,
        ]).lower()

        checks = {
            "goal": bool(re.search(r"^#+\s*why\b", self.proposal, re.M | re.I))
                    or "why" in self.proposal.lower()[:200],
            "scope": bool(re.search(r"what changes|what's changing|scope", self.proposal, re.I)),
            "inputs_outputs": bool(re.search(r"interface|endpoint|input|output|api|request|response", haystack)),
            "data_changes": bool(re.search(r"schema|migration|model|database|data change", haystack)),
            "edge_cases": bool(re.search(r"error|failure|invalid|edge case|raise|throw", haystack))
                          or any(re.search(r"fail|error|invalid", (r["scenario"] or ""), re.I)
                                 for r in self.requirements),
            "acceptance_tests": any(r["scenario"] for r in self.requirements),
            "constraints": bool(re.search(r"constraint|must not|dependenc|performance|security", haystack)),
            "no_change_list": bool(self._extract_no_change_openspec()),
        }
        for name, ok in checks.items():
            (present if ok else missing).append(name)
        return len(present), present, missing

    def _extract_no_change_openspec(self):
        """OpenSpec has no no-change section by default. Only an explicit heading
        is treated as one; absence means the check does not run, not that it
        passed."""
        out = []
        if not self.design:
            return out
        m = re.search(r"^#+\s*(no[- ]change|must not change).*?$(.*?)(?=^#|\Z)",
                      self.design, re.I | re.M | re.S)
        if m:
            out += [t for t in re.findall(r"`([^`]+)`", m.group(2))]
        return sorted(set(out))

    def _extract_files_openspec(self):
        out = set()
        for doc in (self.design, self.proposal):
            for tok in re.findall(r"`([\w./-]+\.\w{1,6})`", doc):
                out.add(tok)
        return out


# Paths that are framework bookkeeping, not delivered code. The Uvik benchmark
# strips these before blind review ("framework folders, spec files, task IDs and
# spec references in comments"), because a review that counts its own scaffolding
# as scope drift is measuring itself.
BOOKKEEPING_PREFIXES = (
    ".kairos/", ".egm/", ".kiro/", "openspec/", ".specify/", "specs/",
    ".claude/", ".cursor/", ".agents/",
)

def _is_bookkeeping(path):
    return path.startswith(BOOKKEEPING_PREFIXES)


def diff_stats(diff_text):
    """Files touched by a unified diff, plus added/removed counts.

    Framework bookkeeping is excluded from the file list; it would otherwise
    register as scope drift in every single review.
    """
    files, added, removed = [], 0, 0
    current = None
    for line in diff_text.splitlines():
        if line.startswith("+++ b/"):
            current = line[6:].strip()
            if current not in files and not _is_bookkeeping(current):
                files.append(current)
        elif line.startswith("+++ /dev/null"):
            current = None
        elif line.startswith("+") and not line.startswith("+++"):
            added += 1
        elif line.startswith("-") and not line.startswith("---"):
            removed += 1
    return {"files": files, "added": added, "removed": removed}


DEPENDENCY_LINE_RE = re.compile(
    r'^\+?\s*["\']?[@A-Za-z0-9_./-]+["\']?\s*[:=]\s*["\'][~^>=<]*\s*\d+\.\d+'
)
MANIFEST_FILES = ("package.json", "requirements.txt", "pyproject.toml",
                  "Cargo.toml", "go.mod", "Gemfile", "composer.json")
SKIP_DIRS = ("node_modules/", "vendor/", ".git/", "dist/", "build/", ".venv/")


def simplicity_findings(diff_text, spec, baseline_lines=200):
    """The one Karpathy guideline a diff can actually check.

    The four guidelines are: think before coding, simplicity first, surgical
    changes, goal-driven execution. Three are already enforced elsewhere:
    surgical changes by the no-change list and scope drift, goal-driven execution
    by the acceptance-criteria check, and think-before-coding by the brainstorm
    brief. Simplicity had no check at all, which is why it was the guideline most
    often violated while everyone nodded at it.

    Two mechanical proxies, both labelled as proxies:

      - a dependency added to an existing manifest with no mention in the spec
        (the guideline says no unrequested dependencies)
      - a brand-new source file far larger than the median new file in the same
        diff (the guideline says if 200 lines could be 50, rewrite it)

    Neither can prove the code is overcomplicated. They flag the two shapes where
    overcomplication reliably shows up, and stay silent otherwise, because a
    false accusation of "too complex" is worse than no check.
    """
    findings = []
    added = {}
    current = ""
    for line in diff_text.splitlines():
        if line.startswith("+++ b/"):
            current = line[6:].strip()
            continue
        if not current or any(s in current for s in SKIP_DIRS):
            continue
        if line.startswith("+") and not line.startswith("+++"):
            added.setdefault(current, []).append(line[1:])

    # 1. Unrequested dependency.
    for path, lines in added.items():
        if Path(path).name not in MANIFEST_FILES:
            continue
        spec_text = (spec.text + getattr(spec, "design", "") + getattr(spec, "proposal", ""))
        for raw in lines:
            if not DEPENDENCY_LINE_RE.match(raw):
                continue
            m = re.search(r'["\']?(@?[A-Za-z0-9_./-]+)["\']?\s*[:=]\s*["\']', raw)
            if not m:
                continue
            name = m.group(1)
            if name in ("name", "version", "description", "main", "type", "license"):
                continue
            if name.lower() in spec_text.lower():
                continue
            findings.append({
                "rule": "unrequested_dependency",
                "severity": "minor",
                "detail": f"{name} added to {path} but never mentioned in the spec",
                "evidence": "Karpathy guideline 2 (Simplicity First): no unrequested dependencies",
            })

    # 2. A new file much larger than the other new files in the same diff.
    new_sizes = {p: len(ls) for p, ls in added.items()
                 if p.endswith(CODE_EXT) and len(ls) > 0
                 and not re.search(r"(^|/)(tests?|__tests__|spec)/", p)}
    for p, size in new_sizes.items():
        others = sorted(s for q, s in new_sizes.items() if q != p)
        if not others:
            continue
        # Compare against the others, not the whole set: comparing a file with
        # itself drags the median up and hides exactly the outlier we want.
        median_others = others[len(others) // 2]
        if size > max(baseline_lines, median_others * 3):
            findings.append({
                "rule": "large_new_file",
                "severity": "minor",
                "detail": (f"{p} adds {size} lines, more than 3x every other new "
                           f"file in this change (median {median_others})"),
                "evidence": "Karpathy guideline 2 (Simplicity First): if 200 lines could be 50, rewrite it",
            })

    return findings


# Directory suffixes that mark delivered source, for the size comparison above.
CODE_EXT = (".py", ".ts", ".js", ".tsx", ".jsx", ".go", ".rs", ".rb", ".php",
            ".java", ".kt", ".swift", ".cs", ".c", ".cpp", ".dart")


def _glob_match(path, pattern):
    from fnmatch import fnmatch
    return fnmatch(path, pattern) or fnmatch(path, pattern.rstrip("/") + "/*")


def _words(text):
    """Split identifier-ish text into lowercase word stems.

    `test_withdrawing_more_than_the_limit` must match the criterion
    "withdrawing more than the limit returns 400", so underscores and camelCase
    both count as separators, and words are reduced to a rough stem so that
    `withdraw` matches `withdrawing`. Stemming is deliberately crude: a wrong
    match costs a missed drift warning, a wrong non-match costs a false blocker.
    """
    spaced = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", text)
    out = set()
    for w in re.split(r"[^A-Za-z0-9]+", spaced):
        w = w.lower()
        if len(w) < 4:
            continue
        for suffix in ("ing", "ed", "es", "s"):
            if len(w) - len(suffix) >= 4 and w.endswith(suffix):
                w = w[:-len(suffix)]
                break
        out.add(w)
    return out


def gate(spec, diff_text, allow_fraud_rules=()):
    """Compare a delivered diff against its spec. Returns a verdict + findings.

    Verdicts:
      BLOCKED  a declared invariant was violated, or the spec is too weak to trust
      REPAIR   the change does not match what the spec said it would do
      READY    the diff is consistent with a complete spec

    Order matters: a no-change violation outranks everything, because it means
    the change broke something the author explicitly promised not to touch.
    """
    from kairos_cli import scan_diff_text

    findings = []
    completeness, present, missing = spec.completeness()
    stats = diff_stats(diff_text)

    # 1. Spec strength. Below the measured threshold the spec predicted nothing,
    #    so "it matches the spec" is not evidence of anything.
    if completeness < COMPLETENESS_THRESHOLD:
        findings.append({
            "rule": "spec_too_weak",
            "severity": "blocker",
            "detail": (f"spec covers {completeness}/8 checklist items "
                       f"(threshold {COMPLETENESS_THRESHOLD}); missing: {', '.join(missing)}"),
            "evidence": "Uvik SDD Benchmark 2026: specs with 6+ items merged 89.3% vs 60.0%",
        })

    # 2. No-change list violation.
    violations = []
    for pattern in spec.no_change:
        for f in stats["files"]:
            if _glob_match(f, pattern) or pattern in f:
                violations.append((pattern, f))
    for pattern, f in violations:
        findings.append({
            "rule": "no_change_violation",
            "severity": "blocker",
            "detail": f"spec says `{pattern}` must not change; diff modifies {f}",
            "evidence": f"spec: {spec.path.name}",
        })

    # 3. Scope: files touched that the spec never mentioned.
    if spec.declared_files:
        undeclared = [f for f in stats["files"] if f not in spec.declared_files]
        if undeclared:
            findings.append({
                "rule": "scope_drift",
                "severity": "major",
                "detail": (f"{len(undeclared)} file(s) touched but not named in the spec: "
                           f"{', '.join(undeclared[:6])}"
                           + (" …" if len(undeclared) > 6 else "")),
                "evidence": f"spec declares {len(spec.declared_files)} file(s)",
            })

    # 4. Drift: acceptance criteria with no corresponding test in the diff.
    #    This looks at every added line in a test file, not only at added test
    #    functions. A rewritten test body (try/except -> pytest.raises) still
    #    proves the criterion, and judging only new `def test_` lines reported
    #    drift on work that had in fact been verified.
    if spec.criteria:
        added_in_tests = []
        current_file = ""
        for line in diff_text.splitlines():
            if line.startswith("+++ b/"):
                current_file = line[6:].strip()
                continue
            if line.startswith("+") and not line.startswith("+++"):
                if re.search(r"(^|/)(tests?|__tests__|spec)/|test_|_test\.|\.test\.|\.spec\.", current_file):
                    added_in_tests.append(line[1:])
        unmatched = []
        for crit in spec.criteria:
            crit_words = _words(crit)
            if not crit_words:
                continue
            if not any(crit_words & _words(line) for line in added_in_tests):
                unmatched.append(crit)
        if len(unmatched) == len(spec.criteria):
            findings.append({
                "rule": "spec_drift",
                "severity": "major",
                "detail": (f"none of {len(spec.criteria)} acceptance criteria map to a test "
                           f"added in this diff"),
                "evidence": "Uvik SDD Benchmark 2026: 7.9% of merged spec tickets drifted from their spec",
            })
        elif unmatched:
            findings.append({
                "rule": "spec_drift",
                "severity": "minor",
                "detail": f"{len(unmatched)}/{len(spec.criteria)} criteria have no matching test: "
                          + "; ".join(u[:60] for u in unmatched[:3]),
                "evidence": "matching is by keyword overlap; review manually",
            })
    else:
        findings.append({
            "rule": "no_acceptance_criteria",
            "severity": "major",
            "detail": "spec lists no checkable acceptance criteria, so drift cannot be detected",
            "evidence": "nothing to compare the diff against",
        })

    # 5. Fraud patterns. Only the rules with measured non-zero precision run by
    #    default; see docs/EXTERNAL_VALIDATION.md.
    for v in scan_diff_text(diff_text, enable_rules=allow_fraud_rules):
        findings.append({
            "rule": f"fraud:{v['fraud_type']}",
            "severity": "major" if v["fraud_type"] in ("assert_deletion", "weakened_test_skip") else "minor",
            "detail": f"{v['file']}: {v['line'][:100]}",
            "evidence": v["description"],
        })

    # 6. Simplicity. The only Karpathy guideline with no check anywhere else.
    findings.extend(simplicity_findings(diff_text, spec))

    if any(f["severity"] == "blocker" for f in findings):
        verdict = "BLOCKED"
    elif any(f["severity"] in ("major",) for f in findings):
        verdict = "REPAIR"
    else:
        verdict = "READY"

    return {
        "verdict": verdict,
        "spec": str(spec.path),
        "completeness": completeness,
        "completeness_present": present,
        "completeness_missing": missing,
        "criteria": len(spec.criteria),
        "declared_files": len(spec.declared_files),
        "diff": stats,
        "findings": findings,
    }


def fit_test(answers):
    """Uvik Spec Fit Test: should this ticket have had a spec at all?

    The benchmark found no gain on bug-fix, refactor and test-writing tickets, and
    a real cost. Answering honestly here is what keeps the process from becoming
    ceremony on small work.
    """
    score = sum(1 for a in answers if a)
    return {
        "score": score,
        "of": len(FIT_STATEMENTS),
        "threshold": FIT_THRESHOLD,
        "verdict": "SPEC" if score >= FIT_THRESHOLD else "NO_SPEC",
        "statements": FIT_STATEMENTS,
    }


def main():  # pragma: no cover - thin CLI wrapper, exercised via kairos_cli
    import argparse
    ap = argparse.ArgumentParser(description="KAIROS gate: verify a diff against its spec")
    ap.add_argument("--spec", required=True)
    ap.add_argument("--diff", default=None, help="diff file; omit to read stdin")
    ap.add_argument("--base", default=None, help="git base ref; computes the diff itself")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    spec = parse_spec(args.spec)
    if args.base:
        import subprocess
        diff_text = subprocess.run(["git", "diff", f"{args.base}...HEAD"],
                                   capture_output=True, text=True).stdout
    elif args.diff:
        diff_text = Path(args.diff).read_text(encoding="utf-8", errors="replace")
    else:
        import sys
        diff_text = sys.stdin.read()

    result = gate(spec, diff_text)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"VERDICT: {result['verdict']}")
        print(f"  spec completeness: {result['completeness']}/8 (needs {COMPLETENESS_THRESHOLD})")
        for f in result["findings"]:
            print(f"  [{f['severity']}] {f['rule']}: {f['detail']}")
    return 0 if result["verdict"] == "READY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
