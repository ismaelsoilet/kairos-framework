#!/usr/bin/env python3
"""
KAIROS Adversarial Attack Suite - Round 3 (SureForge Hardening & Post-Audit Verification)
Validates that all 9 critical findings from the adversarial red-team audit are permanently sealed.
"""

import sys
import os
import shutil
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from kairos_cli import (
    scan_diff_text, load_state, save_state, cmd_dial, cmd_audit,
    cmd_rollback, cmd_mutate, get_kairos_dir, StateLock
)

def test_worktree_audit_detection():
    print("▶ VETOR 1: Testando Auditoria Adversária em Worktree Ativa...")
    state = load_state(REPO_ROOT)
    test_wt_name = "test_round3_wt"
    wt_path = get_kairos_dir(REPO_ROOT) / "worktrees" / test_wt_name
    
    # Clean up if exists
    if wt_path.exists():
        subprocess.run(["git", "worktree", "remove", "--force", str(wt_path)], cwd=REPO_ROOT, capture_output=True)
        subprocess.run(["git", "branch", "-D", f"kairos/{test_wt_name}"], cwd=REPO_ROOT, capture_output=True)

    # Create worktree
    create_res = subprocess.run(["git", "worktree", "add", "-b", f"kairos/{test_wt_name}", str(wt_path)],
                                cwd=REPO_ROOT, capture_output=True, text=True)
    if create_res.returncode != 0:
        print(f"  ❌ Falha ao criar worktree: {create_res.stderr}")
        return False

    state["active_worktree"] = str(wt_path)
    save_state(state, REPO_ROOT)

    try:
        # Inject blatant fraud inside worktree
        bad_code_file = wt_path / "tests" / "test_sneaky.py"
        bad_code_file.parent.mkdir(parents=True, exist_ok=True)
        bad_code_file.write_text("import pytest\n@pytest.mark.skip\ndef test_fraud():\n    pass\n", encoding="utf-8")

        # Run cmd_audit from root
        class MockAuditArgs:
            base = "main"
            worktree = None
            root_only = False

        exit_code = cmd_audit(MockAuditArgs())
        caught = (exit_code != 0)
        print(f"  [Ataque 1A] Detecção de Fraude em Worktree Ativa a partir da Raiz: {'🛡️ BARROU (Exit code != 0)' if caught else '❌ VAZOU (Falha fatal!)'}")
        return caught
    finally:
        subprocess.run(["git", "worktree", "remove", "--force", str(wt_path)], cwd=REPO_ROOT, capture_output=True)
        subprocess.run(["git", "branch", "-D", f"kairos/{test_wt_name}"], cwd=REPO_ROOT, capture_output=True)
        state["active_worktree"] = None
        save_state(state, REPO_ROOT)

def test_production_code_non_interference():
    print("\n▶ VETOR 2: Testando Imunidade a Falsos Positivos em Código de Produção...")
    
    diff_ml = """diff --git a/src/pipeline.py b/src/pipeline.py
--- a/src/pipeline.py
+++ b/src/pipeline.py
@@ -10,3 +10,4 @@
+    clf = RandomForestClassifier()
+    clf.fit(X_train, y_train)
"""
    v_ml = scan_diff_text(diff_ml)
    ok_ml = len(v_ml) == 0

    diff_db = """diff --git a/src/user.repo.ts b/src/user.repo.ts
--- a/src/user.repo.ts
+++ b/src/user.repo.ts
@@ -15,3 +15,4 @@
+    const users = await query.skip(offset).take(limit).getMany();
"""
    v_db = scan_diff_text(diff_db)
    ok_db = len(v_db) == 0

    diff_val = """diff --git a/src/schema.ts b/src/schema.ts
--- a/src/schema.ts
+++ b/src/schema.ts
@@ -5,3 +5,4 @@
+    const statusSchema = Joi.string().only("ACTIVE", "INACTIVE");
"""
    v_val = scan_diff_text(diff_val)
    ok_val = len(v_val) == 0

    all_ok = ok_ml and ok_db and ok_val
    print(f"  [Ataque 2A] `model.fit()` em `pipeline.py`: {'🛡️ PERMITIDO (Zero violações)' if ok_ml else '❌ BLOQUEADO (Falso positivo!)'}")
    print(f"  [Ataque 2B] `query.skip()` em `user.repo.ts`: {'🛡️ PERMITIDO (Zero violações)' if ok_db else '❌ BLOQUEADO (Falso positivo!)'}")
    print(f"  [Ataque 2C] `Joi.only()` em `schema.ts`: {'🛡️ PERMITIDO (Zero violações)' if ok_val else '❌ BLOQUEADO (Falso positivo!)'}")
    return all_ok

def test_magic_comment_bypass_resistance():
    print("\n▶ VETOR 3: Testando Resistência ao Bypass do Comentário Mágico (# FRAUD_PATTERNS)...")
    
    diff_magic = """diff --git a/tests/test_gateway.ts b/tests/test_gateway.ts
--- a/tests/test_gateway.ts
+++ b/tests/test_gateway.ts
@@ -10,3 +10,4 @@
+    it.only('skips real checks', () => {}); // FRAUD_PATTERNS
"""
    violations = scan_diff_text(diff_magic)
    caught = any(v["fraud_type"] == "weakened_test_skip" for v in violations)
    print(f"  [Ataque 3A] Linha de teste focal com `# FRAUD_PATTERNS`: {'🛡️ BARROU (Sem bypass)' if caught else '❌ VAZOU (Bypass vulnerável!)'}")
    return caught

def test_advanced_catch_evasions():
    print("\n▶ VETOR 4: Testando Detecção de Evasões Avançadas de Exceções Vazias...")

    diff_py_none = """diff --git a/src/task.py b/src/task.py
--- a/src/task.py
+++ b/src/task.py
@@ -10,3 +10,4 @@
+    except Exception:
+        None
"""
    v_none = scan_diff_text(diff_py_none)
    ok_none = any(v["fraud_type"] == "silent_failure_empty_catch" for v in v_none)

    diff_js_void = """diff --git a/src/worker.ts b/src/worker.ts
--- a/src/worker.ts
+++ b/src/worker.ts
@@ -10,3 +10,5 @@
+    } catch (e) {
+        void 0;
+    }
"""
    v_void = scan_diff_text(diff_js_void)
    ok_void = any(v["fraud_type"] == "silent_failure_empty_catch" for v in v_void)

    all_ok = ok_none and ok_void
    print(f"  [Ataque 4A] Python `except Exception: None`: {'🛡️ BARROU' if ok_none else '❌ VAZOU'}")
    print(f"  [Ataque 4B] JS/TS `catch (e) {{ void 0; }}`: {'🛡️ BARROU' if ok_void else '❌ VAZOU'}")
    return all_ok

def test_dial_security_overrides():
    print("\n▶ VETOR 5: Testando Priorização Semântica de Segurança e Finanças no Dial...")
    orig_state = load_state(REPO_ROOT)
    try:
        class MockArgsWire:
            description = ["Create", "button", "to", "execute", "funds", "wire", "transfer"]
            force_gamma = False
            force_beta = False

        cmd_dial(MockArgsWire())
        state = load_state(REPO_ROOT)
        mode_wire = state.get("mode")
        ok_wire = mode_wire == "gamma"

        class MockArgsSql:
            description = ["Fix", "critical", "SQL", "injection", "vulnerability", "in", "search", "endpoint"]
            force_gamma = False
            force_beta = False

        cmd_dial(MockArgsSql())
        state = load_state(REPO_ROOT)
        mode_sql = state.get("mode")
        ok_sql = mode_sql == "gamma"

        all_ok = ok_wire and ok_sql
        print(f"  [Ataque 5A] 'button to wire transfer funds' -> Modo: {mode_wire} {'🛡️ PRIORIZOU GAMMA' if ok_wire else '❌ ERRO (Caiu em Alpha!)'}")
        print(f"  [Ataque 5B] 'SQL injection vulnerability' -> Modo: {mode_sql} {'🛡️ PRIORIZOU GAMMA' if ok_sql else '❌ ERRO (Caiu em Beta!)'}")
        return all_ok
    finally:
        save_state(orig_state, REPO_ROOT)

def main():
    print("==========================================================================")
    print("⚔️  KAIROS RED TEAM ADVERSARIAL ATTACK SUITE - ROUND 3 (SUREFORGE HARDENED)")
    print("==========================================================================")
    orig_state = load_state(REPO_ROOT)
    try:
        res1 = test_worktree_audit_detection()
        res2 = test_production_code_non_interference()
        res3 = test_magic_comment_bypass_resistance()
        res4 = test_advanced_catch_evasions()
        res5 = test_dial_security_overrides()

        all_passed = res1 and res2 and res3 and res4 and res5
        print("\n==========================================================================")
        print("📊 RESUMO DOS ACHADOS DO ROUND 3")
        print("==========================================================================")
        if all_passed:
            print("🏆 100% DOS VETORES ADVERSÁRIOS FORAM NEUTRALIZADOS COM SUCESSO!")
            print("   • Worktree audit: Ativa e sem furos.")
            print("   • Falsos positivos: Eliminados em bibliotecas ML/DB/Schema.")
            print("   • Backdoor de comentário: Removido.")
            print("   • Evasões de exceção (None, void 0): Detectadas.")
            print("   • Priorização de segurança e finanças: Garantida em MODE GAMMA.")
        else:
            print("⚠️ Algum vetor ainda vazou. Inspecione os relatórios acima.")
        print("==========================================================================")
        sys.exit(0 if all_passed else 1)
    finally:
        save_state(orig_state, REPO_ROOT)

if __name__ == "__main__":
    main()
