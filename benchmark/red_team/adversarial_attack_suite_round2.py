#!/usr/bin/env python3
"""
KAIROS Adversarial Attack Suite - Round 2 (Extreme Deep-Vector Stress Testing)
Testing advanced vectors: Path Traversal, Infinite Loop Mutants, Negative Token Injection,
Focus/XFail test evasion, Test Function Deletion, and Language Mutation Support.
"""

import sys
import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from kairos_cli import scan_diff_text, load_state, save_state, cmd_token, cmd_spec, MUTATION_OPS

def test_vector_path_traversal_and_injection():
    print("▶ VETOR 1: Testando Path Traversal e Injeção de Caracteres em Nomes de Spec e Branch...")
    orig_state = load_state(REPO_ROOT)
    
    # Attack 1A: Path traversal in spec name
    traversal_name = "../../../tmp/kairos_evil_escape"
    class MockArgs:
        name = traversal_name
    
    try:
        cmd_spec(MockArgs())
        evil_path = Path("/tmp/kairos_evil_escape")
        escaped = evil_path.exists()
        if escaped:
            import shutil
            shutil.rmtree(evil_path, ignore_errors=True)
        # Clean up change directories created inside .kairos/changes
        for p in (REPO_ROOT / ".kairos" / "changes").glob("*kairos_evil_escape*"):
            if p.is_dir():
                import shutil
                shutil.rmtree(p, ignore_errors=True)
        print(f"  [Ataque 1A] `kairos spec ../../../tmp/kairos_evil_escape`: {'❌ VAZOU (Escreveu fora do repo!)' if escaped else '🛡️ BARROU'}")
    except Exception as e:
        print(f"  [Ataque 1A] Exceção levantada: 🛡️ BARROU ({e})")
        escaped = False
    finally:
        save_state(orig_state, REPO_ROOT)

    # Attack 1B: Invalid branch characters in name
    invalid_names = ["bad..branch", "head~1", "branch with spaces", "test:colon"]
    sanitized_properly = True
    for bname in invalid_names:
        # Check if sanitize function or validation exists in scripts/kairos_cli.py
        # If not, git worktree add fails with fatal git error or corrupts ref
        pass

    return not escaped

def test_vector_infinite_loop_in_mutation():
    print("\n▶ VETOR 2: Testando Resiliência a Loops Infinitos no Motor de Mutação (Timeout)...")
    
    # Inspect if subprocess.run in cmd_mutate has timeout parameter
    cli_code = (REPO_ROOT / "scripts" / "kairos_cli.py").read_text(encoding="utf-8")
    has_timeout = "timeout=" in cli_code
    print(f"  [Ataque 2A] Verificação de `timeout` no `subprocess.run(test_cmd)` do `cmd_mutate`: {'🛡️ POSSUI TIMEOUT' if has_timeout else '❌ VAZOU (Sem timeout! Processo trava para sempre em loop infinito)'}")
    return has_timeout

def test_vector_token_budget_tampering():
    print("\n▶ VETOR 3: Testando Manipulação Maliciosa de Tokens (Valores Negativos)...")
    
    state = load_state(REPO_ROOT)
    initial_consumed = state.get("total_tokens_consumed", 0)
    
    class MockTokenArgs:
        action = "add"
        count = -999999
        stage = None

    try:
        cmd_token(MockTokenArgs())
        updated_state = load_state(REPO_ROOT)
        new_consumed = updated_state.get("total_tokens_consumed", 0)
        negative_allowed = new_consumed < initial_consumed
    except ValueError as e:
        negative_allowed = False

    # Restore state
    state["total_tokens_consumed"] = initial_consumed
    save_state(state, REPO_ROOT)

    print(f"  [Ataque 3A] Injeção de `kairos token add -999999`: {'❌ VAZOU (Permitiu tokens negativos!)' if negative_allowed else '🛡️ BARROU (Rejeitou valor negativo com erro explícito)'}")
    return not negative_allowed

def test_vector_advanced_audit_evasions():
    print("\n▶ VETOR 4: Testando Evasões Avançadas de Auditoria de Diffs...")

    # Attack 4A: test.only / describe.only / it.only (Focus tests disable all other tests)
    diff_only = """diff --git a/tests/test_auth.ts b/tests/test_auth.ts
--- a/tests/test_auth.ts
+++ b/tests/test_auth.ts
@@ -10,3 +10,3 @@
-    it('validates user session', () => {
+    it.only('validates user session', () => {
"""
    v_only = scan_diff_text(diff_only)
    caught_only = any(v["fraud_type"] == "weakened_test_skip" for v in v_only)
    print(f"  [Ataque 4A] `it.only` / `test.only`: {'🛡️ BARROU' if caught_only else '❌ VAZOU (Ignorou teste focal que silencia a suíte!)'}")

    # Attack 4B: pytest.xfail / @pytest.mark.xfail (Expected failure silences breakage)
    diff_xfail = """diff --git a/tests/test_payment.py b/tests/test_payment.py
--- a/tests/test_payment.py
+++ b/tests/test_payment.py
@@ -12,2 +12,4 @@
+@pytest.mark.xfail(reason="temporary skip")
 def test_charge():
+    pytest.xfail("silence failure")
"""
    v_xfail = scan_diff_text(diff_xfail)
    caught_xfail = any(v["fraud_type"] == "weakened_test_skip" for v in v_xfail)
    print(f"  [Ataque 4B] `@pytest.mark.xfail` e `pytest.xfail`: {'🛡️ BARROU' if caught_xfail else '❌ VAZOU (Permitiu mascarar falha com xfail!)'}")

    # Attack 4C: Deletion of entire test function without assert keyword
    diff_func_del = """diff --git a/tests/test_security.py b/tests/test_security.py
--- a/tests/test_security.py
+++ b/tests/test_security.py
@@ -30,5 +30,1 @@
-def test_rate_limiting_under_ddos():
-    client = make_client()
-    res = client.flood_requests()
-    verify_rate_limited(res)
+print("DDOS test temporarily removed")
"""
    v_func_del = scan_diff_text(diff_func_del)
    caught_func_del = any(v["fraud_type"] in ("assert_deletion", "weakened_test_skip", "test_deletion") for v in v_func_del)
    print(f"  [Ataque 4C] Deleção de função de teste inteira (`- def test_...`): {'🛡️ BARROU' if caught_func_del else '❌ VAZOU (Deletou teste sem ser notado!)'}")

    # Attack 4D: JS/TS boolean mutation support
    js_sample = "    const isValid = true;\n    if (hasAccess == false) return false;\n"
    matched_js = any("true" in p or "false" in p for p, r in MUTATION_OPS)
    print(f"  [Ataque 4D] Suporte a mutação de booleanos JS/TS (`true`/`false`): {'🛡️ SUPORTADO' if matched_js else '⚠️ AUSENTE (Apenas `True`/`False` Python suportado)'}")

    return {
        "4A": caught_only,
        "4B": caught_xfail,
        "4C": caught_func_del,
        "4D": matched_js
    }

def main():
    print("==========================================================================")
    print("⚔️  KAIROS RED TEAM ADVERSARIAL ATTACK SUITE - ROUND 2 (DEEP PENETRATION)")
    print("==========================================================================")
    orig_state = load_state(REPO_ROOT)
    try:
        res1 = test_vector_path_traversal_and_injection()
        res2 = test_vector_infinite_loop_in_mutation()
        res3 = test_vector_token_budget_tampering()
        res4 = test_vector_advanced_audit_evasions()

        print("\n==========================================================================")
        print("📊 RESUMO DOS ACHADOS DO ROUND 2")
        print("==========================================================================")
        deficiencies = []
        if not res1:
            deficiencies.append("DEF-R2-01: Path traversal em nomes de spec permite escapar da pasta .kairos/changes/")
        if not res2:
            deficiencies.append("DEF-R2-02: cmd_mutate não possui timeout e trava em loops infinitos gerados por mutação.")
        if not res3:
            deficiencies.append("DEF-R2-03: cmd_token aceita valores negativos, permitindo mascarar estouro de tokens.")
        if not res4.get("4A"):
            deficiencies.append("DEF-R2-04: it.only / test.only / describe.only não são detectados pelo auditor.")
        if not res4.get("4B"):
            deficiencies.append("DEF-R2-05: pytest.xfail e @pytest.mark.xfail não são detectados.")
        if not res4.get("4C"):
            deficiencies.append("DEF-R2-06: Deleção de funções inteiras de teste (- def test_...) não é detectada se não contiver assert explícito.")
        if not res4.get("4D"):
            deficiencies.append("DEF-R2-07: Motor de mutação não muta booleanos JavaScript/TypeScript (true/false).")

        print(f"Total de deficiências de Rodada 2 detectadas: {len(deficiencies)}")
        for d in deficiencies:
            print(f"  ⚠️  {d}")
        print("==========================================================================")
    finally:
        save_state(orig_state, REPO_ROOT)

if __name__ == "__main__":
    main()
