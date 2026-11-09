import unittest
import sys
import os
import json
import shutil
import subprocess
from pathlib import Path

# Add scripts directory to path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from kairos_cli import (
    cmd_spec, cmd_audit, StateLock, scan_diff_text,
    save_state, load_state, get_kairos_dir,
)


# Rules that are off by default (0% precision on external code, see
# docs/EXTERNAL_VALIDATION.md). Tests of those rules must opt in, because the
# default is deliberately conservative.
ALL_RULES = (
    "silent_failure_empty_catch", "guard_removal", "phantom_stub",
    "weakened_assertion", "mock_substitution", "unconditional_accept",
)

class TestKairosFeatures(unittest.TestCase):

    def setUp(self):
        self.original_cwd = os.getcwd()
        os.chdir(REPO_ROOT)
        self.orig_state = load_state(REPO_ROOT)

    def tearDown(self):
        save_state(self.orig_state, REPO_ROOT)
        os.chdir(self.original_cwd)

    def test_diff_scanner_catches_comment_separated_empty_catch(self):
        """RED TEAM DEF-01: Comments or blank lines between except and pass must be caught."""
        diff = """diff --git a/src/service.py b/src/service.py
--- a/src/service.py
+++ b/src/service.py
@@ -10,3 +10,5 @@
+    except Exception as err:
+        # Silently bypass for now
+        pass
"""
        violations = scan_diff_text(diff, enable_rules=ALL_RULES)
        fraud_types = [v["fraud_type"] for v in violations]
        self.assertIn("silent_failure_empty_catch", fraud_types)

    def test_diff_scanner_catches_multiline_js_empty_catch(self):
        """RED TEAM CRITICAL-01.2: JS/TS multiline catch blocks must be caught."""
        diff = """diff --git a/src/auth.ts b/src/auth.ts
--- a/src/auth.ts
+++ b/src/auth.ts
@@ -20,3 +20,6 @@
+    try {
+        doSomething();
+    } catch (error) {
+        // ignore error
+    }
"""
        violations = scan_diff_text(diff, enable_rules=ALL_RULES)
        fraud_types = [v["fraud_type"] for v in violations]
        self.assertIn("silent_failure_empty_catch", fraud_types)

    def test_diff_scanner_catches_es2019_optional_catch_binding(self):
        """RED TEAM CRITICAL-01.2: JS/TS catch {} without parentheses."""
        diff = """diff --git a/src/auth.js b/src/auth.js
--- a/src/auth.js
+++ b/src/auth.js
@@ -10,2 +10,4 @@
+    catch {
+    }
"""
        violations = scan_diff_text(diff, enable_rules=ALL_RULES)
        fraud_types = [v["fraud_type"] for v in violations]
        self.assertIn("silent_failure_empty_catch", fraud_types)

    def test_diff_scanner_prevents_false_positive_on_assert_refactoring(self):
        """RED TEAM CRITICAL-01.3: Updating/refactoring an assert in a test must NOT be flagged as deletion."""
        diff = """diff --git a/tests/test_math.py b/tests/test_math.py
--- a/tests/test_math.py
+++ b/tests/test_math.py
@@ -5,2 +5,2 @@
-    assert old_calc(2) == 4
+    assert new_calc(2) == 4
"""
        violations = scan_diff_text(diff)
        fraud_types = [v["fraud_type"] for v in violations]
        self.assertNotIn("assert_deletion", fraud_types)

    def test_diff_scanner_flags_genuine_assert_deletion(self):
        """RED TEAM CRITICAL-01.3: Deleting an assert without replacement MUST be flagged."""
        diff = """diff --git a/tests/test_math.py b/tests/test_math.py
--- a/tests/test_math.py
+++ b/tests/test_math.py
@@ -5,2 +5,1 @@
-    assert security_check() is True
+    print("skipping security check")
"""
        violations = scan_diff_text(diff)
        fraud_types = [v["fraud_type"] for v in violations]
        self.assertIn("assert_deletion", fraud_types)

    def test_diff_scanner_catches_stubs_returning_trivial_constants(self):
        """RED TEAM DEF-02: Stubs returning None, {}, [], '' must be caught as phantom stubs."""
        diff = """diff --git a/src/service.py b/src/service.py
--- a/src/service.py
+++ b/src/service.py
@@ -15,2 +15,4 @@
+def verify_signature(token):
+    # Not implemented yet
+    return None
"""
        violations = scan_diff_text(diff, enable_rules=ALL_RULES)
        fraud_types = [v["fraud_type"] for v in violations]
        self.assertIn("phantom_stub", fraud_types)

if __name__ == "__main__":
    unittest.main()
