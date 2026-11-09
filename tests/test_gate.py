"""Tests for the spec↔diff gate.

Each test asserts that a specific check can FAIL. A gate that only ever says READY
is not a gate, which is the failure this project already made once.
"""

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from kairos_gate import Spec, gate, fit_test, diff_stats, COMPLETENESS_THRESHOLD


COMPLETE_SPEC = """# Feature: withdraw limits

## Goal
Reject withdrawals above the account limit.

## Scope
In scope: the withdraw endpoint. Out of scope: deposits.

## Inputs and outputs
Input: amount (int). Output: 200 with balance, or 400 with reason.

## Data changes
None.

## Edge cases
Zero, negative, and amounts above the limit.

## Acceptance tests
- [ ] withdrawing more than the limit returns 400
- [ ] withdrawing exactly the limit succeeds

## Constraints
Must not add a dependency.

## No-change list
- `src/deposits.py`
- `src/legacy/*`
"""

WEAK_SPEC = """# Feature: withdraw limits

## Notes
Reject withdrawals above the account limit.
"""


class TestCompleteness(unittest.TestCase):
    def test_complete_spec_meets_threshold(self):
        s = Spec("x.md", COMPLETE_SPEC)
        score, present, missing = s.completeness()
        self.assertGreaterEqual(score, COMPLETENESS_THRESHOLD,
                                f"complete spec scored {score}/8, missing {missing}")

    def test_weak_spec_scores_low(self):
        s = Spec("x.md", WEAK_SPEC)
        score, _, _ = s.completeness()
        self.assertLess(score, COMPLETENESS_THRESHOLD)

    def test_criteria_extracted(self):
        s = Spec("x.md", COMPLETE_SPEC)
        self.assertEqual(len(s.criteria), 2)
        self.assertIn("withdrawing more than the limit returns 400", s.criteria)

    def test_no_change_list_extracted(self):
        s = Spec("x.md", COMPLETE_SPEC)
        self.assertIn("src/deposits.py", s.no_change)

    def test_declared_files_extracted(self):
        spec = COMPLETE_SPEC.replace(
            "## Scope",
            "## Implementation\n\n- `src/withdraw.py`\n- `tests/test_withdraw.py`\n\n## Scope")
        s = Spec("x.md", spec)
        self.assertIn("src/withdraw.py", s.declared_files)


CLEAN_DIFF = """diff --git a/src/withdraw.py b/src/withdraw.py
--- a/src/withdraw.py
+++ b/src/withdraw.py
@@ -1,2 +1,5 @@
 def withdraw(amount):
+    if amount > limit:
+        raise ValueError('over limit')
     return balance
diff --git a/tests/test_withdraw.py b/tests/test_withdraw.py
--- a/tests/test_withdraw.py
+++ b/tests/test_withdraw.py
@@ -1,2 +1,4 @@
+def test_withdrawing_more_than_the_limit_returns_400():
+    assert withdraw(limit + 1) == 400
"""


class TestGateCanFail(unittest.TestCase):
    def test_weak_spec_blocks(self):
        result = gate(Spec("weak.md", WEAK_SPEC), CLEAN_DIFF)
        self.assertEqual(result["verdict"], "BLOCKED")
        self.assertIn("spec_too_weak", [f["rule"] for f in result["findings"]])

    def test_no_change_violation_blocks(self):
        diff = CLEAN_DIFF + """diff --git a/src/deposits.py b/src/deposits.py
--- a/src/deposits.py
+++ b/src/deposits.py
@@ -1,2 +1,2 @@
-def deposit(x):
+def deposit(x, fee):
"""
        result = gate(Spec("x.md", COMPLETE_SPEC), diff)
        self.assertEqual(result["verdict"], "BLOCKED")
        self.assertIn("no_change_violation", [f["rule"] for f in result["findings"]])

    def test_scope_drift_requires_repair(self):
        spec = Spec("x.md", COMPLETE_SPEC.replace(
            "## Scope",
            "## Implementation\n\n- `src/withdraw.py`\n- `tests/test_withdraw.py`\n\n## Scope"))
        diff = CLEAN_DIFF + """diff --git a/src/untold.py b/src/untold.py
--- a/src/untold.py
+++ b/src/untold.py
@@ -1,1 +1,2 @@
+x = 1
"""
        result = gate(spec, diff)
        self.assertIn("scope_drift", [f["rule"] for f in result["findings"]])
        self.assertNotEqual(result["verdict"], "READY")

    def test_no_scope_declared_skips_scope_check(self):
        """A spec that names no files cannot produce scope drift. The check is
        skipped rather than assumed to pass silently — it reports nothing."""
        result = gate(Spec("x.md", COMPLETE_SPEC), CLEAN_DIFF)
        self.assertNotIn("scope_drift", [f["rule"] for f in result["findings"]])

    def test_no_test_for_criteria_is_drift(self):
        diff = """diff --git a/src/withdraw.py b/src/withdraw.py
--- a/src/withdraw.py
+++ b/src/withdraw.py
@@ -1,2 +1,3 @@
 def withdraw(amount):
+    return amount
     return balance
"""
        result = gate(Spec("x.md", COMPLETE_SPEC), diff)
        self.assertIn("spec_drift", [f["rule"] for f in result["findings"]])

    def test_clean_delivery_is_ready(self):
        spec = Spec("x.md", COMPLETE_SPEC.replace(
            "## Scope",
            "## Implementation\n\n- `src/withdraw.py`\n- `tests/test_withdraw.py`\n\n## Scope"))
        result = gate(spec, CLEAN_DIFF)
        self.assertEqual(result["verdict"], "READY",
                         f"expected READY, findings={result['findings']}")

    def test_assert_deletion_is_caught(self):
        diff = """diff --git a/tests/test_withdraw.py b/tests/test_withdraw.py
--- a/tests/test_withdraw.py
+++ b/tests/test_withdraw.py
@@ -1,3 +1,0 @@
-def test_withdrawing_more_than_the_limit_returns_400():
-    assert withdraw(limit + 1) == 400
-    assert True
"""
        result = gate(Spec("x.md", COMPLETE_SPEC), diff)
        rules = [f["rule"] for f in result["findings"]]
        self.assertTrue(any(r.startswith("fraud:") for r in rules),
                        f"assert deletion not caught: {rules}")


class TestRegressions(unittest.TestCase):
    """Bugs found by running the gate on a real branch, not by reasoning."""

    def test_bookkeeping_is_not_scope_drift(self):
        """`.kairos/state.json` and `.egm/*` are framework output. Counting them as
        scope drift made every single review report REPAIR."""
        diff = CLEAN_DIFF + """diff --git a/.kairos/state.json b/.kairos/state.json
--- a/.kairos/state.json
+++ b/.kairos/state.json
@@ -1,1 +1,1 @@
-{"stage":"IDLE"}
+{"stage":"VERIFIED"}
"""
        st = diff_stats(diff)
        self.assertNotIn(".kairos/state.json", st["files"])
        self.assertIn("src/withdraw.py", st["files"])

    def test_rewritten_test_body_still_counts_for_drift(self):
        """A test rewritten from try/except to pytest.raises proves the criterion.
        Judging only newly added `def test_` lines reported drift on verified work."""
        spec = Spec("x.md", COMPLETE_SPEC.replace(
            "## Scope",
            "## Implementation\n\n- `src/withdraw.py`\n- `tests/test_withdraw.py`\n\n## Scope"))
        diff = """diff --git a/tests/test_withdraw.py b/tests/test_withdraw.py
--- a/tests/test_withdraw.py
+++ b/tests/test_withdraw.py
@@ -1,5 +1,4 @@
 def test_withdrawing_more_than_the_limit_returns_400():
-    try:
+    with pytest.raises(ValueError, match='over limit'):
         withdraw(150)
-    except ValueError:
-        assert True
"""
        result = gate(spec, diff)
        self.assertNotIn("spec_drift", [f["rule"] for f in result["findings"]])

    def test_backticked_word_is_not_a_no_change_path(self):
        """Regression: prose like `gate` was read as a path and blocked every diff
        that touched a file with that word in its name."""
        spec = COMPLETE_SPEC.replace(
            "- `src/deposits.py`\n- `src/legacy/*`",
            "The `gate` command must not break. `src/deposits.py` must not change.")
        s = Spec("x.md", spec)
        self.assertIn("src/deposits.py", s.no_change)
        self.assertNotIn("gate", s.no_change)

    def test_pytest_raises_counts_as_assertion(self):
        """Replacing try/except+assert with pytest.raises is a strict improvement;
        it must not be reported as an assertion deletion."""
        diff = """diff --git a/tests/test_w.py b/tests/test_w.py
--- a/tests/test_w.py
+++ b/tests/test_w.py
@@ -1,5 +1,4 @@
 def test_x():
-    try:
+    with pytest.raises(ValueError):
         withdraw(150)
-    except ValueError:
-        assert True
"""
        result = gate(Spec("x.md", COMPLETE_SPEC), diff)
        self.assertNotIn("fraud:assert_deletion", [f["rule"] for f in result["findings"]])


class TestOpenSpecAdapter(unittest.TestCase):
    """Regression: the README claimed OpenSpec support before it existed.
    A raw delta spec scored 0/8, which would have called every OpenSpec change
    'too weak' — the format answers different questions, not fewer."""

    def _make_change(self, tmp, with_design=True):
        root = Path(tmp) / "openspec" / "changes" / "add-dark-mode"
        (root / "specs" / "ui").mkdir(parents=True)
        (root / "proposal.md").write_text(
            "## Why\nUsers want dark mode.\n\n"
            "## What Changes\n- Add a theme toggle\n- Persist the choice\n", encoding="utf-8")
        (root / "tasks.md").write_text("## 1. Implementation\n- [ ] 1.1 Add provider\n", encoding="utf-8")
        spec = root / "specs" / "ui" / "spec.md"
        spec.write_text(
            "## ADDED Requirements\n\n"
            "### Requirement: Theme selection\n"
            "The app SHALL let users switch themes.\n\n"
            "#### Scenario: User toggles dark mode\n"
            "- **WHEN** the user clicks the toggle\n"
            "- **THEN** the app switches to dark mode\n", encoding="utf-8")
        if with_design:
            (root / "design.md").write_text(
                "# Design\n\n## Interfaces\n`useTheme()` returns `{theme, toggle}`.\n\n"
                "## Edge cases\n- localStorage unavailable: fall back to memory\n"
                "- invalid stored value: ignore\n\n"
                "## Constraints\nNo new dependency. Must not change the palette.\n\n"
                "## Files\n- `src/theme.tsx`\n- `tests/theme.test.tsx`\n", encoding="utf-8")
        return spec

    def test_delta_spec_is_parsed_as_openspec_not_generic(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            spec = self._make_change(tmp)
            from kairos_gate import parse_spec, OpenSpec
            parsed = parse_spec(spec)
            self.assertIsInstance(parsed, OpenSpec)
            self.assertEqual(len(parsed.requirements), 1)
            self.assertEqual(parsed.requirements[0]["op"], "ADDED")
            self.assertEqual(parsed.requirements[0]["scenario"], "User toggles dark mode")

    def test_scenario_becomes_an_acceptance_criterion(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            spec = self._make_change(tmp)
            from kairos_gate import parse_spec
            parsed = parse_spec(spec)
            self.assertTrue(any("dark mode" in c.lower() for c in parsed.criteria))

    def test_full_openspec_change_meets_the_threshold(self):
        """With design.md — which OpenSpec recommends — the change scores 6/8.
        The gate was never meant to demand a format OpenSpec does not use."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            spec = self._make_change(tmp)
            from kairos_gate import parse_spec, COMPLETENESS_THRESHOLD
            parsed = parse_spec(spec)
            score, present, missing = parsed.completeness()
            self.assertGreaterEqual(score, COMPLETENESS_THRESHOLD,
                                    f"scored {score}/8, missing {missing}")

    def test_delta_only_change_is_flagged_weak(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            spec = self._make_change(tmp, with_design=False)
            from kairos_gate import parse_spec, COMPLETENESS_THRESHOLD
            parsed = parse_spec(spec)
            score, _, _ = parsed.completeness()
            self.assertLess(score, COMPLETENESS_THRESHOLD)


class TestSimplicity(unittest.TestCase):
    """Karpathy guideline 2. The other three guidelines are enforced elsewhere in
    the gate (no-change list, scope drift, acceptance criteria); this one had no
    check at all, which is why it was the most nodded-at and least followed."""

    def test_unrequested_dependency_is_flagged(self):
        diff = """diff --git a/package.json b/package.json
--- a/package.json
+++ b/package.json
@@ -10,3 +10,4 @@
   "dependencies": {
     "react": "19.0.0",
+    "lodash": "^4.17.0",
   }
"""
        result = gate(Spec("x.md", COMPLETE_SPEC), diff)
        rules = [f["rule"] for f in result["findings"]]
        self.assertIn("unrequested_dependency", rules)

    def test_requested_dependency_is_not_flagged(self):
        """If the spec names it, adding it is the plan being followed."""
        spec = COMPLETE_SPEC.replace(
            "## Constraints", "## Constraints\nThe change adds `lodash`.")
        diff = """diff --git a/package.json b/package.json
--- a/package.json
+++ b/package.json
@@ -10,3 +10,4 @@
   "dependencies": {
     "react": "19.0.0",
+    "lodash": "^4.17.0",
   }
"""
        result = gate(Spec("x.md", spec), diff)
        self.assertNotIn("unrequested_dependency", [f["rule"] for f in result["findings"]])

    def test_oversized_new_file_is_flagged(self):
        big = "\n".join(f"+line_{i} = {i}" for i in range(260))
        small = "\n".join(f"+x_{i} = {i}" for i in range(20))
        diff = (f"diff --git a/src/huge.py b/src/huge.py\n--- /dev/null\n+++ b/src/huge.py\n"
                f"@@ -0,0 +1,260 @@\n{big}\n"
                f"diff --git a/src/small.py b/src/small.py\n--- /dev/null\n+++ b/src/small.py\n"
                f"@@ -0,0 +1,20 @@\n{small}\n")
        result = gate(Spec("x.md", COMPLETE_SPEC), diff)
        rules = [f["rule"] for f in result["findings"]]
        self.assertIn("large_new_file", rules,
                      f"260 lines next to a 20-line file was not flagged: {rules}")

    def test_simplicity_findings_are_minor_not_blocking(self):
        """A style proxy must never block a delivery. Blocking is reserved for
        contract violations."""
        diff = """diff --git a/package.json b/package.json
--- a/package.json
+++ b/package.json
@@ -10,3 +10,4 @@
   "dependencies": {
     "react": "19.0.0",
+    "lodash": "^4.17.0",
   }
"""
        result = gate(Spec("x.md", COMPLETE_SPEC), diff)
        dep = [f for f in result["findings"] if f["rule"] == "unrequested_dependency"]
        self.assertTrue(dep)
        self.assertEqual(dep[0]["severity"], "minor")
        self.assertNotEqual(result["verdict"], "BLOCKED")

    def test_node_modules_is_ignored(self):
        diff = """diff --git a/node_modules/x/index.js b/node_modules/x/index.js
--- /dev/null
+++ b/node_modules/x/index.js
@@ -0,0 +1,3 @@
+a = 1
"""
        from kairos_gate import simplicity_findings
        self.assertEqual(simplicity_findings(diff, Spec("x.md", COMPLETE_SPEC)), [])


class TestJudgeReplacements(unittest.TestCase):
    """The four items from fable-judge that the gate did not cover.

    Adopting the framework would have meant a second set of verdict names,
    a second report format, and another dependency to keep current. Each item
    was a few lines of check instead.
    """

    def test_debug_statement_is_debris(self):
        diff = """diff --git a/src/app.py b/src/app.py
--- a/src/app.py
+++ b/src/app.py
@@ -1,2 +1,3 @@
 def run():
+    breakpoint()
     return 1
"""
        result = gate(Spec("x.md", COMPLETE_SPEC), diff)
        debris = [f for f in result["findings"] if f["rule"] == "debris"]
        self.assertTrue(debris)
        self.assertEqual(debris[0]["severity"], "major",
                         "a debugger left in delivered code halts execution")

    def test_scratch_file_is_debris(self):
        diff = """diff --git a/scratch_notes.py b/scratch_notes.py
--- /dev/null
+++ b/scratch_notes.py
@@ -0,0 +1,2 @@
+tmp = 1
"""
        result = gate(Spec("x.md", COMPLETE_SPEC), diff)
        self.assertIn("debris", [f["rule"] for f in result["findings"]])

    def test_print_is_not_debris(self):
        """`print` and `console.error` are legitimate output. Flagging them is
        how a checker gets turned off."""
        diff = """diff --git a/src/cli.py b/src/cli.py
--- a/src/cli.py
+++ b/src/cli.py
@@ -1,2 +1,3 @@
 def main():
+    print("usage: app <file>")
"""
        result = gate(Spec("x.md", COMPLETE_SPEC), diff)
        self.assertNotIn("debris", [f["rule"] for f in result["findings"]])

    def test_outward_command_is_major(self):
        diff = """diff --git a/Makefile b/Makefile
--- a/Makefile
+++ b/Makefile
@@ -1,2 +1,3 @@
 deploy:
+	terraform apply -auto-approve
"""
        result = gate(Spec("x.md", COMPLETE_SPEC), diff)
        outward = [f for f in result["findings"] if f["rule"] == "outward_command"]
        self.assertTrue(outward, "terraform apply not flagged")
        self.assertEqual(outward[0]["severity"], "major")

    def test_failing_verification_blocks(self):
        """The one claim a diff cannot settle. This is the core of 'a report is a
        claim, not evidence'."""
        verification = {"command": "pytest -q", "exit_code": 1,
                        "duration_s": 2.1, "tail": ["2 failed, 7 passed"]}
        result = gate(Spec("x.md", COMPLETE_SPEC), CLEAN_DIFF, verification=verification)
        self.assertEqual(result["verdict"], "BLOCKED")
        self.assertIn("verification_failed", [f["rule"] for f in result["findings"]])

    def test_passing_verification_does_not_block(self):
        verification = {"command": "pytest -q", "exit_code": 0,
                        "duration_s": 1.0, "tail": ["9 passed"]}
        result = gate(Spec("x.md", COMPLETE_SPEC), CLEAN_DIFF, verification=verification)
        self.assertNotIn("verification_failed", [f["rule"] for f in result["findings"]])

    def test_timeout_counts_as_failure(self):
        verification = {"command": "pytest -q", "exit_code": "TIMEOUT",
                        "duration_s": 600, "tail": ["exceeded 600s"]}
        result = gate(Spec("x.md", COMPLETE_SPEC), CLEAN_DIFF, verification=verification)
        self.assertIn("verification_failed", [f["rule"] for f in result["findings"]])

    def test_run_verification_captures_real_exit_code(self):
        from kairos_gate import run_verification
        ok = run_verification("exit 0")
        bad = run_verification("exit 3")
        self.assertEqual(ok["exit_code"], 0)
        self.assertEqual(bad["exit_code"], 3)
        self.assertIn("command", ok)


class TestDiffStats(unittest.TestCase):
    def test_counts_files_and_lines(self):
        st = diff_stats(CLEAN_DIFF)
        self.assertIn("src/withdraw.py", st["files"])
        self.assertIn("tests/test_withdraw.py", st["files"])
        self.assertGreater(st["added"], 0)

    def test_deleted_file_not_counted_as_touched(self):
        diff = """diff --git a/gone.py b/gone.py
--- a/gone.py
+++ /dev/null
@@ -1,1 +0,0 @@
-x = 1
"""
        st = diff_stats(diff)
        self.assertNotIn("gone.py", st["files"])


class TestFitTest(unittest.TestCase):
    def test_small_change_expects_no_spec(self):
        result = fit_test([False, False, False, False, False, False])
        self.assertEqual(result["verdict"], "NO_SPEC",
                         "a one-file bugfix should not require a spec")

    def test_large_change_expects_spec(self):
        result = fit_test([True, True, True, False, False, False])
        self.assertEqual(result["verdict"], "SPEC")


class TestParseSpec(unittest.TestCase):
    def test_egm_style_design_doc_is_parsed(self):
        egm = """# Webhook delivery

## The Problem
Deliveries fail silently.

## Goals
Report failures.

## Non-Goals
Retry logic.

## Technical Plan
Touches `src/webhook.py`.

## Implementation
- [ ] failed delivery is recorded
- [ ] duplicate event is rejected

## Edge cases
Timeout, duplicate, 500.

## Acceptance tests
- [ ] failed delivery appears in the log
"""
        s = Spec("design.md", egm)
        score, present, missing = s.completeness()
        self.assertGreaterEqual(score, 5, f"EGM doc scored {score}, missing {missing}")
        self.assertGreater(len(s.criteria), 0)


if __name__ == "__main__":
    unittest.main()
