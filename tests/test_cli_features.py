import unittest
import sys
import os
import shutil
import subprocess
from pathlib import Path

# Add scripts directory to path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from kairos_cli import (
    cmd_status, cmd_rollback, cmd_mutate, cmd_token, cmd_spec,
    cmd_update, cmd_registry, cmd_lesson, cmd_scout,
    parse_project_dependencies, HIGH_RISK_CUTOFF_PACKAGES,
    scan_diff_text, save_state, load_state, get_kairos_dir, MUTATION_OPS
)

class TestKairosFeatures(unittest.TestCase):

    def setUp(self):
        self.original_cwd = os.getcwd()
        os.chdir(REPO_ROOT)

    def tearDown(self):
        os.chdir(self.original_cwd)

    def test_visual_dashboard_flag_exists(self):
        """Test that --dashboard can be called on status."""
        class MockArgs:
            header_only = False
            dashboard = True
        exit_code = cmd_status(MockArgs())
        self.assertEqual(exit_code, 0)

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
        violations = scan_diff_text(diff)
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
        violations = scan_diff_text(diff)
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
        violations = scan_diff_text(diff)
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
        violations = scan_diff_text(diff)
        fraud_types = [v["fraud_type"] for v in violations]
        self.assertIn("phantom_stub", fraud_types)

    def test_mutation_operators_match_pep8_spaced_operators(self):
        """RED TEAM CRITICAL-02.1: Mutation operators must match standard spaced code like `a == b`."""
        import re
        sample = "    if user_id == expected_id and count >= 10:\n"
        matched = False
        for pattern, repl in MUTATION_OPS:
            if re.search(pattern, sample):
                matched = True
                break
        self.assertTrue(matched, "No mutation operator matched `user_id == expected_id and count >= 10`!")

    def test_atomic_state_save(self):
        """RED TEAM RISK-02: State save must not leave a corrupted file on interrupted write."""
        state = load_state(REPO_ROOT)
        state["_test_atomic_key"] = "atomic_value_123"
        save_state(state, REPO_ROOT)
        reloaded = load_state(REPO_ROOT)
        self.assertEqual(reloaded.get("_test_atomic_key"), "atomic_value_123")

    # -----------------------------------------------------------------------
    # ROUND 2 ADVERSARIAL STRESS TESTS
    # -----------------------------------------------------------------------

    def test_spec_name_sanitization_rejects_path_traversal(self):
        """ROUND 2 CRITICAL-01: cmd_spec must sanitize path traversal and keep files inside .kairos/changes."""
        class MockArgs:
            name = "../../../tmp/evil_escape_test"
        cmd_spec(MockArgs())
        evil_leak = Path("/tmp/evil_escape_test")
        self.assertFalse(evil_leak.exists(), "Path traversal escaped into /tmp!")
        # Clean up test directories created in .kairos/changes
        for p in (REPO_ROOT / ".kairos" / "changes").glob("*evil_escape_test*"):
            if p.is_dir():
                shutil.rmtree(p)

    def test_token_add_rejects_negative_values(self):
        """ROUND 2 RISK-01: cmd_token add must reject negative values."""
        class MockTokenArgs:
            action = "add"
            count = -50000
            stage = None
        with self.assertRaises(ValueError):
            cmd_token(MockTokenArgs())

    def test_diff_scanner_catches_focused_tests_dot_only(self):
        """ROUND 2 RISK-03.1: it.only and describe.only silence the entire suite and must be blocked."""
        diff = """diff --git a/tests/test_auth.ts b/tests/test_auth.ts
--- a/tests/test_auth.ts
+++ b/tests/test_auth.ts
@@ -10,3 +10,3 @@
-    it('validates user token', () => {
+    it.only('validates user token', () => {
"""
        violations = scan_diff_text(diff)
        fraud_types = [v["fraud_type"] for v in violations]
        self.assertIn("weakened_test_skip", fraud_types)

    def test_diff_scanner_catches_pytest_xfail(self):
        """ROUND 2 RISK-03.2: @pytest.mark.xfail masks broken tests and must be blocked."""
        diff = """diff --git a/tests/test_auth.py b/tests/test_auth.py
--- a/tests/test_auth.py
+++ b/tests/test_auth.py
@@ -5,2 +5,3 @@
+@pytest.mark.xfail(reason="temporarily failing")
 def test_security():
"""
        violations = scan_diff_text(diff)
        fraud_types = [v["fraud_type"] for v in violations]
        self.assertIn("weakened_test_skip", fraud_types)

    def test_diff_scanner_catches_completely_deleted_test_files(self):
        """ROUND 2 RISK-02: Deleting a test file (+++ /dev/null) must detect assertion deletion."""
        diff = """diff --git a/tests/test_critical.py b/tests/test_critical.py
deleted file mode 100644
--- a/tests/test_critical.py
+++ /dev/null
@@ -1,5 +0,0 @@
-def test_audit():
-    assert verify_signature() is True
-    assert check_permissions() == 200
"""
        violations = scan_diff_text(diff)
        fraud_types = [v["fraud_type"] for v in violations]
        self.assertIn("assert_deletion", fraud_types)

    def test_diff_scanner_catches_tautological_assert_laundering(self):
        """ROUND 2 RISK-04: Replacing assertions with `assert True` or `assert 1 == 1` must be blocked."""
        diff = """diff --git a/tests/test_auth.py b/tests/test_auth.py
--- a/tests/test_auth.py
+++ b/tests/test_auth.py
@@ -5,2 +5,2 @@
-    assert authenticate(bad_token) is False
+    assert True
"""
        violations = scan_diff_text(diff)
        fraud_types = [v["fraud_type"] for v in violations]
        self.assertIn("tautological_assertion", fraud_types)

    def test_mutation_operators_support_js_ts_operators(self):
        """ROUND 2 SIMPLIFY-01: Mutation engine must support JS/TS boolean (true/false) and strict equality."""
        import re
        sample_js = "const isValid = true;\nif (status === 200 && isAuth) return false;\n"
        matched = False
        for pattern, repl in MUTATION_OPS:
            if re.search(pattern, sample_js):
                matched = True
                break
        self.assertTrue(matched, "No mutation operator matched JS `true`, `===`, `&&`, or `false`!")

    def test_registry_discovers_agents_and_skills(self):
        """Test that kairos registry successfully enumerates agents and skills."""
        class MockArgs:
            pass
        exit_code = cmd_registry(MockArgs())
        self.assertEqual(exit_code, 0)

    def test_update_executes_health_check(self):
        """Test that kairos update can check upstream remote."""
        class MockArgs:
            skip_self_test = True
        exit_code = cmd_update(MockArgs())
        self.assertEqual(exit_code, 0)

    def test_lesson_add_and_list(self):
        """Test that kairos lesson can record a new lesson and list existing ones."""
        lessons_path = REPO_ROOT / ".kairos" / "lessons.md"
        backup_content = lessons_path.read_text(encoding="utf-8") if lessons_path.exists() else None
        try:
            class MockAddArgs:
                action = "add"
                title = "Test Jest InBand"
                trap = "Jest races on shared SQLite"
                rule = "Run jest with --runInBand"
            exit_code = cmd_lesson(MockAddArgs())
            self.assertEqual(exit_code, 0)
            self.assertTrue(lessons_path.exists())
            self.assertIn("Test Jest InBand", lessons_path.read_text(encoding="utf-8"))

            class MockListArgs:
                action = "list"
            exit_code = cmd_lesson(MockListArgs())
            self.assertEqual(exit_code, 0)
        finally:
            if backup_content is not None:
                lessons_path.write_text(backup_content, encoding="utf-8")
            elif lessons_path.exists():
                lessons_path.unlink()

    def test_scout_detects_cutoff_risk_packages(self):
        """Test that parse_project_dependencies extracts cutoff packages from manifest."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            pkg_json = tmppath / "package.json"
            pkg_json.write_text('{"dependencies": {"next": "15.0.1", "react": "19.0.0", "lodash": "4.17.21"}}', encoding="utf-8")
            
            manifests, deps = parse_project_dependencies(tmppath)
            self.assertIn("package.json", manifests)
            self.assertIn("next", deps)
            self.assertIn("react", deps)
            self.assertEqual(deps["next"][1], "15.0.1")
            
            # Check risk matching
            risks = [k for k in deps if k in HIGH_RISK_CUTOFF_PACKAGES]
            self.assertIn("next", risks)
            self.assertIn("react", risks)

    def test_scout_cli_execution(self):
        """Test that kairos scout runs cleanly."""
        class MockArgs:
            all = True
            save_spec = False
        exit_code = cmd_scout(MockArgs())
        self.assertEqual(exit_code, 0)

    def test_diff_scanner_catches_obsolete_model_in_markdown(self):
        """Audit scanner must catch hallucinated or obsolete model references in docs."""
        diff = """diff --git a/docs/guide.md b/docs/guide.md
--- a/docs/guide.md
+++ b/docs/guide.md
@@ -10,3 +10,4 @@
+We recommend using Gemini 3.8 or OpenAI Codex for this task.
"""
        violations = scan_diff_text(diff)
        fraud_types = [v["fraud_type"] for v in violations]
        self.assertIn("obsolete_ai_model_reference", fraud_types)

    def test_diff_scanner_catches_obsolete_model_in_code(self):
        """Audit scanner must catch deprecated model references in source code."""
        diff = """diff --git a/src/llm.py b/src/llm.py
--- a/src/llm.py
+++ b/src/llm.py
@@ -5,2 +5,3 @@
+MODEL_NAME = "text-davinci-003"
"""
        violations = scan_diff_text(diff)
        fraud_types = [v["fraud_type"] for v in violations]
        self.assertIn("obsolete_ai_model_reference", fraud_types)

if __name__ == "__main__":
    unittest.main()
