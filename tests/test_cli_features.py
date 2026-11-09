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
    cmd_status, cmd_rollback, cmd_mutate, cmd_token, cmd_spec,
    cmd_update, cmd_registry, cmd_lesson, cmd_scout, cmd_dial, cmd_audit,
    parse_project_dependencies, HIGH_RISK_CUTOFF_PACKAGES, StateLock,
    scan_diff_text, save_state, load_state, get_kairos_dir, MUTATION_OPS
)

class TestKairosFeatures(unittest.TestCase):

    def setUp(self):
        self.original_cwd = os.getcwd()
        os.chdir(REPO_ROOT)
        self.orig_state = load_state(REPO_ROOT)

    def tearDown(self):
        save_state(self.orig_state, REPO_ROOT)
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
        try:
            state["_test_atomic_key"] = "atomic_value_123"
            save_state(state, REPO_ROOT)
            reloaded = load_state(REPO_ROOT)
            self.assertEqual(reloaded.get("_test_atomic_key"), "atomic_value_123")
        finally:
            if "_test_atomic_key" in state:
                del state["_test_atomic_key"]
                save_state(state, REPO_ROOT)

    # -----------------------------------------------------------------------
    # ROUND 2 ADVERSARIAL STRESS TESTS
    # -----------------------------------------------------------------------

    def test_spec_name_sanitization_rejects_path_traversal(self):
        """ROUND 2 CRITICAL-01: cmd_spec must sanitize path traversal and keep files inside .kairos/changes."""
        orig_state = load_state(REPO_ROOT)
        class MockArgs:
            name = "../../../tmp/evil_escape_test"
        try:
            cmd_spec(MockArgs())
            evil_leak = Path("/tmp/evil_escape_test")
            self.assertFalse(evil_leak.exists(), "Path traversal escaped into /tmp!")
        finally:
            save_state(orig_state, REPO_ROOT)
            # Clean up test directories created in .kairos/changes
            for p in (REPO_ROOT / ".kairos" / "changes").glob("*evil_escape_test*"):
                if p.is_dir():
                    shutil.rmtree(p)

    def test_token_import_reads_real_usage_and_rejects_empty_log(self):
        """v1.2: token counts must come from a real usage log, never a manual increment.

        `token add` was removed because an agent incrementing its own counter is the
        exact 'false completion' this project claims to detect.
        """
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "usage.jsonl"
            log.write_text(
                '{"usage": {"inputTokens": 1000, "outputTokens": 250, "cacheReadTokens": 5000, "costUsd": 0.01}}\n'
                '{"message": {"usage": {"input_tokens": 2000, "output_tokens": 500}}}\n',
                encoding="utf-8",
            )

            class ImportArgs:
                action = "import"
                usage = str(log)
                stage = None

            before = load_state(REPO_ROOT)
            try:
                self.assertEqual(cmd_token(ImportArgs()), 0)
                state = load_state(REPO_ROOT)
                self.assertEqual(state["total_tokens_consumed"], 3750,
                                 "active tokens must be input+output from the log")
                self.assertEqual(state["measured_usage"]["records"], 2)
                self.assertEqual(state["measured_usage"]["input"], 3000)
                self.assertIn("source_sha256", state["measured_usage"])
            finally:
                save_state(before, REPO_ROOT)

            empty = Path(tmp) / "empty.jsonl"
            empty.write_text('{"type": "message"}\n', encoding="utf-8")

            class EmptyArgs:
                action = "import"
                usage = str(empty)
                stage = None

            self.assertNotEqual(cmd_token(EmptyArgs()), 0,
                                "an import with no usage records must fail, not silently report zero")

    def test_audit_requires_mutation_evidence_before_verified(self):
        """v1.2: a clean diff alone must not grant VERIFIED. Test strength must be proven."""
        import tempfile
        k_dir = get_kairos_dir(REPO_ROOT)
        kmutant = k_dir / "kmutant_latest.json"
        backup = kmutant.read_bytes() if kmutant.exists() else None
        before = load_state(REPO_ROOT)
        try:
            if kmutant.exists():
                kmutant.unlink()
            with tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
                subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=repo, check=True)
                subprocess.run(["git", "config", "user.name", "t"], cwd=repo, check=True)
                (repo / "a.py").write_text("x = 1\n", encoding="utf-8")
                subprocess.run(["git", "add", "."], cwd=repo, check=True)
                subprocess.run(["git", "commit", "-qm", "init"], cwd=repo, check=True)
                (repo / "b.py").write_text("def ok():\n    return 1\n", encoding="utf-8")
                subprocess.run(["git", "add", "."], cwd=repo, check=True)

                class Args:
                    base = "main"
                    worktree = str(repo)
                    root_only = False
                    allow_file = []

                prev = os.getcwd()
                os.chdir(repo)
                try:
                    code = cmd_audit(Args())
                finally:
                    os.chdir(prev)
                self.assertNotEqual(code, 0,
                                    "audit granted VERIFIED with no mutation report present")
                report = json.loads((repo / ".kairos" / "audit_latest.json").read_text(encoding="utf-8"))
                self.assertEqual(report["verdict"], "REPAIR")
                self.assertEqual(report["mutation_gate"], "FAILED")
        finally:
            if backup is not None:
                kmutant.write_bytes(backup)
            elif kmutant.exists():
                kmutant.unlink()
            save_state(before, REPO_ROOT)

    def test_dial_force_beta_overrides_gamma_keyword(self):
        """v1.2: --force-beta must win over a gamma keyword in the description."""
        class Args:
            description = ["adjust", "the", "token", "label", "css", "button", "padding"]
            force_gamma = False
            force_beta = True
        before = load_state(REPO_ROOT)
        try:
            self.assertEqual(cmd_dial(Args()), 0)
            self.assertEqual(load_state(REPO_ROOT)["mode"], "beta")
        finally:
            save_state(before, REPO_ROOT)

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
+We recommend using gpt-3.5-turbo or OpenAI Codex for this task.
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

    def test_diff_scanner_allows_model_fit_in_production_code(self):
        """ROUND 3 FIX-01: model.fit(...) in non-test files must NOT trigger weakened_test_skip."""
        diff = """diff --git a/src/train.py b/src/train.py
--- a/src/train.py
+++ b/src/train.py
@@ -10,3 +10,4 @@
+    model = LogisticRegression()
+    model.fit(X_train, y_train)
"""
        violations = scan_diff_text(diff)
        self.assertEqual(violations, [], f"Expected 0 violations for model.fit, got {violations}")

    def test_diff_scanner_allows_query_skip_in_production_code(self):
        """ROUND 3 FIX-02: query.skip(...) in non-test files must NOT trigger weakened_test_skip."""
        diff = """diff --git a/src/user.service.ts b/src/user.service.ts
--- a/src/user.service.ts
+++ b/src/user.service.ts
@@ -10,3 +10,4 @@
+    const query = repo.createQueryBuilder("u").skip(offset).take(limit);
"""
        violations = scan_diff_text(diff)
        self.assertEqual(violations, [], f"Expected 0 violations for query.skip, got {violations}")

    def test_diff_scanner_allows_joi_only_in_production_code(self):
        """ROUND 3 FIX-03: Joi.string().only(...) in non-test files must NOT trigger weakened_test_skip."""
        diff = """diff --git a/src/validation.ts b/src/validation.ts
--- a/src/validation.ts
+++ b/src/validation.ts
@@ -5,3 +5,4 @@
+    const roleSchema = Joi.string().only("ADMIN", "USER");
"""
        violations = scan_diff_text(diff)
        self.assertEqual(violations, [], f"Expected 0 violations for Joi.only, got {violations}")

    def test_diff_scanner_allows_model_fit_in_test_files(self):
        """SUREFORGE REPAIR-01.1: model.fit(...) inside test files must NOT trigger weakened_test_skip."""
        diff = """diff --git a/tests/test_train.py b/tests/test_train.py
--- a/tests/test_train.py
+++ b/tests/test_train.py
@@ -10,3 +10,6 @@
+def test_model_training():
+    model = LogisticRegression()
+    model.fit(X_train, y_train)
+    assert model is not None
"""
        violations = scan_diff_text(diff)
        weakened = [v for v in violations if v["fraud_type"] == "weakened_test_skip"]
        self.assertEqual(weakened, [], f"model.fit in test file incorrectly flagged: {weakened}")

    def test_diff_scanner_allows_query_skip_in_test_files(self):
        """SUREFORGE REPAIR-01.2: query.skip(...) inside test files must NOT trigger weakened_test_skip."""
        diff = """diff --git a/tests/test_pagination.test.ts b/tests/test_pagination.test.ts
--- a/tests/test_pagination.test.ts
+++ b/tests/test_pagination.test.ts
@@ -10,3 +10,6 @@
+test("pagination query", async () => {
+    const results = await query.skip(10).take(5).getMany();
+    expect(results).toBeDefined();
+});
"""
        violations = scan_diff_text(diff)
        weakened = [v for v in violations if v["fraud_type"] == "weakened_test_skip"]
        self.assertEqual(weakened, [], f"query.skip in test file incorrectly flagged: {weakened}")

    def test_diff_scanner_allows_joi_only_in_test_files(self):
        """SUREFORGE REPAIR-01.3: Joi.string().only(...) inside test files must NOT trigger weakened_test_skip."""
        diff = """diff --git a/tests/test_schema.test.ts b/tests/test_schema.test.ts
--- a/tests/test_schema.test.ts
+++ b/tests/test_schema.test.ts
@@ -10,3 +10,6 @@
+it("validates enum", () => {
+    const schema = Joi.string().only("ADMIN", "USER");
+    expect(schema).toBeDefined();
+});
"""
        violations = scan_diff_text(diff)
        weakened = [v for v in violations if v["fraud_type"] == "weakened_test_skip"]
        self.assertEqual(weakened, [], f"Joi.only in test file incorrectly flagged: {weakened}")

    def test_diff_scanner_blocks_magic_comment_bypass(self):
        """ROUND 3 FIX-04: Magic comments like # FRAUD_PATTERNS must NOT exempt lines from audit."""
        diff = """diff --git a/tests/test_secret.ts b/tests/test_secret.ts
--- a/tests/test_secret.ts
+++ b/tests/test_secret.ts
@@ -10,3 +10,4 @@
+    it.only('bypassed', () => {});  # FRAUD_PATTERNS
"""
        violations = scan_diff_text(diff)
        fraud_types = [v["fraud_type"] for v in violations]
        self.assertIn("weakened_test_skip", fraud_types)

    def test_diff_scanner_catches_none_return_continue_silent_catches(self):
        """ROUND 3 FIX-05: Empty catches using None, return, or continue must be blocked."""
        diff_none = """diff --git a/src/worker.py b/src/worker.py
--- a/src/worker.py
+++ b/src/worker.py
@@ -10,3 +10,4 @@
+    except Exception:
+        None
"""
        violations = scan_diff_text(diff_none)
        fraud_types = [v["fraud_type"] for v in violations]
        self.assertIn("silent_failure_empty_catch", fraud_types)

        diff_return = """diff --git a/src/worker.py b/src/worker.py
--- a/src/worker.py
+++ b/src/worker.py
@@ -10,3 +10,4 @@
+    except Exception:
+        return
"""
        violations = scan_diff_text(diff_return)
        fraud_types = [v["fraud_type"] for v in violations]
        self.assertIn("silent_failure_empty_catch", fraud_types)

    def test_diff_scanner_catches_js_void0_empty_catches(self):
        """ROUND 3 FIX-06: Catch blocks with void 0 or bare semicolons must be caught."""
        diff_void = """diff --git a/src/service.ts b/src/service.ts
--- a/src/service.ts
+++ b/src/service.ts
@@ -10,3 +10,5 @@
+    } catch (err) {
+        void 0;
+    }
"""
        violations = scan_diff_text(diff_void)
        fraud_types = [v["fraud_type"] for v in violations]
        self.assertIn("silent_failure_empty_catch", fraud_types)

    def test_diff_scanner_catches_expanded_tautologies(self):
        """ROUND 3 FIX-07: assert 2 == 2, assert not False, expect(true).toBeTruthy() must be blocked."""
        diff = """diff --git a/tests/test_tautology.py b/tests/test_tautology.py
--- a/tests/test_tautology.py
+++ b/tests/test_tautology.py
@@ -10,3 +10,5 @@
+    assert 2 == 2
+    assert not False
"""
        violations = scan_diff_text(diff)
        fraud_types = [v["fraud_type"] for v in violations]
        self.assertIn("tautological_assertion", fraud_types)

    def test_diff_scanner_catches_unittest_skiptest(self):
        """ROUND 3 FIX-08: raise unittest.SkipTest in test files must be caught."""
        diff = """diff --git a/tests/test_auth.py b/tests/test_auth.py
--- a/tests/test_auth.py
+++ b/tests/test_auth.py
@@ -10,3 +10,4 @@
+    raise unittest.SkipTest("skip this test")
"""
        violations = scan_diff_text(diff)
        fraud_types = [v["fraud_type"] for v in violations]
        self.assertIn("weakened_test_skip", fraud_types)

    def test_dial_security_and_financial_prioritization(self):
        """ROUND 3 FIX-09: Financial and security tasks must prioritize MODE GAMMA over button/UI keywords."""
        orig_state = load_state(REPO_ROOT)
        try:
            class MockArgsWire:
                description = ["Create", "button", "to", "execute", "funds", "wire", "transfer"]
                force_gamma = False
                force_beta = False

            cmd_dial(MockArgsWire())
            state = load_state(REPO_ROOT)
            self.assertEqual(state.get("mode"), "gamma")

            class MockArgsSql:
                description = ["Fix", "critical", "SQL", "injection", "vulnerability", "in", "search", "endpoint"]
                force_gamma = False
                force_beta = False

            cmd_dial(MockArgsSql())
            state = load_state(REPO_ROOT)
            self.assertEqual(state.get("mode"), "gamma")
        finally:
            save_state(orig_state, REPO_ROOT)

    def test_state_file_locking_context_manager(self):
        """ROUND 3 FIX-10: StateLock must acquire and release file lock without error."""
        k_dir = get_kairos_dir(REPO_ROOT)
        with StateLock(k_dir):
            state = load_state(REPO_ROOT)
            self.assertIsNotNone(state)
            self.assertIn("mode", state)

    def test_audit_catches_untracked_files_fraud(self):
        """ROUND 3 FIX-11: Untracked new files with test frauds must be audited and blocked."""
        orig_state = load_state(REPO_ROOT)
        temp_file = REPO_ROOT / "tests" / "test_untracked_probe.py"
        try:
            bad_content = "import pytest\n@" + "pytest.mark.skip\ndef test_bad():\n    pass\n"
            temp_file.write_text(bad_content, encoding="utf-8")
            class MockAuditArgs:
                base = "main"
                worktree = None
                root_only = True
            exit_code = cmd_audit(MockAuditArgs())
            self.assertNotEqual(exit_code, 0, "Untracked fraud file was silently ignored by audit!")
        finally:
            if temp_file.exists():
                temp_file.unlink()
            save_state(orig_state, REPO_ROOT)

    def test_worktree_create_and_remove_lifecycle(self):
        """v1.2: worktree create/remove had no test at all. Exiting 0 is not proof it works."""
        from kairos_cli import cmd_worktree
        name = "v12_lifecycle_probe"
        branch = f"kairos/{name}"
        wt_path = get_kairos_dir(REPO_ROOT) / "worktrees" / name
        before = load_state(REPO_ROOT)

        class CreateArgs:
            action = "create"
            name = "v12_lifecycle_probe"

        class RemoveArgs:
            action = "remove"
            name = "v12_lifecycle_probe"

        try:
            self.assertEqual(cmd_worktree(CreateArgs()), 0)
            self.assertTrue(wt_path.is_dir(), "worktree directory was not created")
            branches = subprocess.run(["git", "branch", "--list", branch],
                                      cwd=REPO_ROOT, capture_output=True, text=True).stdout
            self.assertIn(branch, branches, "task branch was not created")

            self.assertEqual(cmd_worktree(RemoveArgs()), 0)
            self.assertFalse(wt_path.is_dir(), "worktree directory survived removal")
            branches = subprocess.run(["git", "branch", "--list", branch],
                                      cwd=REPO_ROOT, capture_output=True, text=True).stdout
            self.assertNotIn(branch, branches, "task branch survived removal")
        finally:
            if wt_path.is_dir():
                subprocess.run(["git", "worktree", "remove", "--force", str(wt_path)],
                               cwd=REPO_ROOT, capture_output=True)
            subprocess.run(["git", "branch", "-D", branch], cwd=REPO_ROOT, capture_output=True)
            save_state(before, REPO_ROOT)

if __name__ == "__main__":
    unittest.main()
