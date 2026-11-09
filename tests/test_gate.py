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
