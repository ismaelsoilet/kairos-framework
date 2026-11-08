#!/usr/bin/env python3
"""
KAIROS CLI: Autonomous Agentic SDLC & Token Governance Engine
Zero-dependency, portable Python 3 CLI for managing the Kairos lifecycle,
delta specs, git worktrees, adversarial diff audits, and multi-harness exports.
"""

import sys
import os
import json
import re
import shutil
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

VERSION = "1.0.0"

# ---------------------------------------------------------------------------
# RISK & CLASSIFICATION MATRICES (The Elastic Dial)
# ---------------------------------------------------------------------------

ALPHA_KEYWORDS = [
    r"\bui\b", r"\bcss\b", r"\bstyle\b", r"\bcor\b", r"\bbot[aã]o\b", r"\bbutton\b",
    r"\btypo\b", r"\bortografi\w*\b", r"\btexto\b", r"\bcopy\b", r"\blayout\b",
    r"\bpadding\b", r"\bmargin\b", r"\balign\b", r"\bresponsiv\w*\b", r"\bcomponente\b",
    r"\bformat\w*\b", r"\blinter\b", r"\bicon\w*\b", r"\bvisual\b", r"\brender\b"
]

GAMMA_KEYWORDS = [
    r"\bauth\b", r"\bautentica\w*\b", r"\blogin\b", r"\bjwt\b", r"\btoken\b", r"\bsess[aã]o\b",
    r"\bseguran[çc]a\b", r"\bsecurity\b", r"\bpermiss\w*\b", r"\brbac\b", r"\bcrypto\b",
    r"\bcripto\w*\b", r"\bpassword\b", r"\bsenha\b", r"\btransa[çc][aã]o\b", r"\btransaction\b",
    r"\bpayment\b", r"\bpagamento\b", r"\bbilling\b", r"\bbanco\b", r"\bdatabase\b",
    r"\bmigra[çc][aã]o\b", r"\bmigration\b", r"\bschema\b", r"\bquebra\b", r"\bbreaking\b",
    r"\barquitetura\b", r"\barchitecture\b", r"\bcore\b", r"\bconcorr[êe]ncia\b", r"\brace condition\b"
]

# ---------------------------------------------------------------------------
# CORE HELPERS
# ---------------------------------------------------------------------------

def find_repo_root():
    """Locate the git repository root, fallback to script's repo, or fallback to current directory."""
    try:
        res = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return Path(res.stdout.strip())
    except Exception:
        # Check if the script itself resides inside a git repository
        script_dir = Path(__file__).resolve().parent
        try:
            res = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True, cwd=script_dir)
            return Path(res.stdout.strip())
        except Exception:
            return Path.cwd()

def get_kairos_dir(root=None):
    if root is None:
        root = find_repo_root()
    return root / ".kairos"

def load_state(root=None):
    k_dir = get_kairos_dir(root)
    state_file = k_dir / "state.json"
    if not state_file.exists():
        return {
            "version": VERSION,
            "created_at": datetime.now().isoformat(),
            "current_stage": "IDLE",
            "active_change": None,
            "mode": "alpha",
            "active_worktree": None,
            "token_budget": 15000,
            "total_tokens_consumed": 0,
            "history": []
        }
    try:
        with open(state_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            if "current_stage" not in data:
                data["current_stage"] = "IDLE"
            if "total_tokens_consumed" not in data:
                data["total_tokens_consumed"] = 0
            return data
    except Exception:
        return {"error": "corrupted_state"}

def save_state(state, root=None):
    if state.get("error") == "corrupted_state":
        return
    k_dir = get_kairos_dir(root)
    k_dir.mkdir(parents=True, exist_ok=True)
    state_file = k_dir / "state.json"
    temp_file = k_dir / f"state.json.{os.getpid()}.tmp"
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno())
    os.replace(temp_file, state_file)

# ---------------------------------------------------------------------------
# COMMAND: INIT
# ---------------------------------------------------------------------------

def cmd_init(args):
    root = find_repo_root()
    k_dir = get_kairos_dir(root)
    (k_dir / "changes").mkdir(parents=True, exist_ok=True)
    (k_dir / "specs").mkdir(parents=True, exist_ok=True)
    (k_dir / "worktrees").mkdir(parents=True, exist_ok=True)
    
    state = load_state(root)
    save_state(state, root)

    # Gitignore for worktrees and temporary state
    gitignore = root / ".gitignore"
    if gitignore.exists():
        content = gitignore.read_text(encoding="utf-8")
        if ".kairos/worktrees" not in content:
            with open(gitignore, "a", encoding="utf-8") as f:
                f.write("\n# KAIROS Local Isolation & State\n.kairos/worktrees/\n.kairos/active_diff.patch\n")

    print(f"✅ KAIROS initialized successfully at: {k_dir}")
    print("📁 Structure:")
    print("   .kairos/changes/   (Active Delta Specs)")
    print("   .kairos/specs/     (Canonical Living Specifications)")
    print("   .kairos/worktrees/ (Isolated Execution Workspaces)")
    print("   .kairos/state.json (Governance & Token State)")
    return 0

# ---------------------------------------------------------------------------
# COMMAND: DIAL (The Elastic Classifier)
# ---------------------------------------------------------------------------

def cmd_dial(args):
    prompt = " ".join(args.description).lower()
    root = find_repo_root()
    state = load_state(root)

    # Scoring mechanism
    alpha_score = sum(1 for p in ALPHA_KEYWORDS if re.search(p, prompt))
    gamma_score = sum(1 for p in GAMMA_KEYWORDS if re.search(p, prompt))

    if gamma_score >= 1 or args.force_gamma:
        mode = "gamma"
        budget = 180000
        desc = "CRITICAL / ENTERPRISE (Full Elephant/Goldfish Spec, Subagents, Zero-Trust Audit)"
        subagents_allowed = 3
    elif alpha_score >= 1 and gamma_score == 0 and not args.force_beta:
        mode = "alpha"
        budget = 15000
        desc = "LITE / UI (In-turn Micro-Delta, Surgical Edit, Diff Sanity Check, Zero Subagents)"
        subagents_allowed = 0
    else:
        mode = "beta"
        budget = 65000
        desc = "STANDARD (Delta Spec in changes/, Git Worktree, TDD, Single Adversarial Check)"
        subagents_allowed = 1

    state["mode"] = mode
    state["token_budget"] = budget
    state["current_stage"] = "CLASSIFIED"
    save_state(state, root)

    print("=================================================================")
    print(f"🎯 KAIROS ELASTIC DIAL CLASSIFICATION: [ MODE {mode.upper()} ]")
    print("=================================================================")
    print(f"• Profile:           {desc}")
    print(f"• Token Budget Cap:  ~{budget:,} tokens (Maximum target)")
    print(f"• Subagent Quota:    {subagents_allowed} external subagents")
    print(f"• Pipeline Workflow:")

    if mode == "alpha":
        print("  1. Spec:  Generate 5-line Micro-Delta directly in conversation.")
        print("  2. Build: Apply minimal surgical edit directly (no worktree required).")
        print("  3. Check: Visual inspection + diff check for a11y/CSS pollution.")
        print("  💡 Tip: Saves ~85% of tokens compared to full pipeline.")
    elif mode == "beta":
        print("  1. Spec:  Scaffold .kairos/changes/<id>/ (proposal, specs, tasks).")
        print("  2. Build: Run in isolated worktree with strict TDD (Red -> Green -> Refactor).")
        print("  3. Check: Verify tests & run automated diff fraud scan (`kairos audit`).")
    else: # gamma
        print("  1. Spec:  Comprehensive Delta Spec + spawn Goldfish reviewer (kairos_critic).")
        print("  2. Build: Isolated worktree + multi-phase TDD + 2-stage verification.")
        print("  3. Check: Adversarial Zero-Trust Audit (6 Frauds) + Evidence Audit Table.")

    print("=================================================================")
    return 0

# ---------------------------------------------------------------------------
# COMMAND: SPEC (Delta Spec Scaffolding)
# ---------------------------------------------------------------------------

PROPOSAL_TEMPLATE = """# Proposal: {name}
* **ID:** {change_id}
* **Created:** {date}
* **Mode:** {mode}
* **Author:** {author}

## 1. Intent & Context
<!-- Why are we doing this? What problem is being solved? -->

## 2. In Scope
- 

## 3. Explicitly Out of Scope (Non-Goals)
- 

## 4. Key Risks & Operational Constraints
- 
"""

SPECS_TEMPLATE = """# Specification & Behavioral Contracts: {name}
* **Change ID:** {change_id}

## 1. Added Behaviors (NEW)
### REQ-01: 
* **Given:** 
* **When:** 
* **Then:** 

## 2. Modified Behaviors (ALTERED)
### MOD-01: 
* **Previous Behavior:** 
* **New Behavior:** 
* **Migration / Retrocompatibility:** 

## 3. Removed Behaviors (DELETED)
- None

## 4. Invariants (Things that MUST NEVER break)
- [ ] Invariant 1: 
"""

DESIGN_TEMPLATE = """# Technical Design: {name}

## 1. Component Architecture & Interfaces
<!-- Which classes, functions, or files are touched? -->

## 2. Data Models / Schemas / Payloads
```typescript
// Define interfaces, types, or DTOs
```

## 3. Error Handling & Edge Cases
| Edge Case | Expected System Response | HTTP / Return Code |
| :--- | :--- | :--- |
| Invalid input | Structured error message | 400 Bad Request |
"""

TASKS_TEMPLATE = """# Implementation Tasks (TDD Breakdown): {name}

- [ ] 1. Test Setup (Red Phase)
  - **Target:** `tests/...`
  - **Command:** `npm test` or `pytest`
  - **Expected Failure:** `AssertionError: Expected ... but got ...`
- [ ] 2. Minimal Implementation (Green Phase)
  - **Target:** `src/...`
  - **Code:** Minimal implementation to turn Test 1 green
- [ ] 3. Refactor Phase
  - **Cleanup:** Remove duplicate code, verify style guides
- [ ] 4. Verification Check
  - **Command:** Verify entire test suite passes without regressions
"""

def sanitize_identifier(name, default="kairos_task"):
    """Strictly sanitize task, spec, and branch names against path traversal and git command injection."""
    if not name:
        return default
    # Strip directory parts to block path traversal
    base_name = os.path.basename(name.strip().replace("\\", "/"))
    # Allow only alphanumeric, underscores and hyphens
    clean = re.sub(r"[^a-zA-Z0-9_\-]", "_", base_name).strip("._-")
    clean = re.sub(r"^-+", "", clean)
    return clean or default

def cmd_spec(args):
    root = find_repo_root()
    state = load_state(root)
    name = sanitize_identifier(args.name)
    change_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{name}"
    
    k_dir = get_kairos_dir(root)
    changes_root = (k_dir / "changes").resolve()
    change_dir = (k_dir / "changes" / change_id).resolve()

    # Strict path traversal check
    if not change_dir.is_relative_to(changes_root):
        raise ValueError(f"Path traversal detected: {args.name}")

    change_dir.mkdir(parents=True, exist_ok=True)

    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    mode = state.get("mode", "beta")
    author = os.environ.get("USER", "engineer")

    (change_dir / "proposal.md").write_text(PROPOSAL_TEMPLATE.format(name=name, change_id=change_id, date=date_str, mode=mode, author=author), encoding="utf-8")
    (change_dir / "specs.md").write_text(SPECS_TEMPLATE.format(name=name, change_id=change_id), encoding="utf-8")
    (change_dir / "design.md").write_text(DESIGN_TEMPLATE.format(name=name), encoding="utf-8")
    (change_dir / "tasks.md").write_text(TASKS_TEMPLATE.format(name=name), encoding="utf-8")
    (change_dir / "evidence.md").write_text(f"# Evidence Audit Table: {name}\n\n| Item | Requisito | Comando Executado | Resultado Observado | Status |\n| :--- | :--- | :--- | :--- | :--- |\n", encoding="utf-8")

    state["active_change"] = change_id
    state["current_stage"] = "SPECIFYING"
    save_state(state, root)

    print(f"✅ Delta Spec initialized at: {change_dir.relative_to(root)}")
    print(f"📝 Files generated:")
    print(f"   • proposal.md (Problem & boundaries)")
    print(f"   • specs.md    (Behavioral contracts Added/Modified)")
    print(f"   • design.md   (Technical choices & schema)")
    print(f"   • tasks.md    (TDD task breakdown)")
    print(f"   • evidence.md (Audit table ready for verifications)")
    print(f"\n💡 Next Step: Edit the files, then run `kairos worktree create` to implement!")
    return 0

# ---------------------------------------------------------------------------
# COMMAND: WORKTREE (Workspace Isolation)
# ---------------------------------------------------------------------------

def cmd_worktree(args):
    root = find_repo_root()
    state = load_state(root)
    action = args.action

    if action == "create":
        raw_name = args.name or state.get("active_change") or "kairos_task"
        name = sanitize_identifier(raw_name)
        branch_name = f"kairos/{name}"
        worktrees_root = (get_kairos_dir(root) / "worktrees").resolve()
        worktree_path = (worktrees_root / name).resolve()

        if not worktree_path.is_relative_to(worktrees_root):
            raise ValueError(f"Path traversal detected in worktree: {args.name}")

        if worktree_path.exists():
            print(f"⚠️ Worktree already exists at {worktree_path}")
            return 1

        print(f"📦 Creating isolated git worktree at {worktree_path.relative_to(root)}...")
        try:
            subprocess.run(["git", "worktree", "add", "-b", branch_name, str(worktree_path)], check=True)
            
            # Auto-link shared project assets and dependencies (env, node_modules, venv)
            for shared_name in [".env", ".env.local", ".venv", "node_modules", "vendor"]:
                source_item = root / shared_name
                target_link = worktree_path / shared_name
                if source_item.exists() and not target_link.exists():
                    try:
                        os.symlink(source_item, target_link)
                    except OSError as err:
                        print(f"ℹ️ Optional link for {shared_name} skipped: {err}")

            state["active_worktree"] = str(worktree_path)
            state["current_stage"] = "BUILDING"
            save_state(state, root)
            print(f"✅ Isolated worktree ready on branch '{branch_name}'.")
            print(f"👉 Navigate with: cd {worktree_path}")
            return 0
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to create worktree: {e}")
            return 1

    elif action == "remove":
        name = args.name or (Path(state.get("active_worktree", "")).name if state.get("active_worktree") else None)
        if not name:
            print("❌ No active worktree to remove.")
            return 1
        worktree_path = get_kairos_dir(root) / "worktrees" / name
        branch_name = f"kairos/{name}"
        print(f"🗑️ Removing worktree at {worktree_path}...")
        try:
            subprocess.run(["git", "worktree", "remove", "--force", str(worktree_path)], check=True)
            # Clean up the associated task branch so it can be cleanly recreated later
            subprocess.run(["git", "branch", "-D", branch_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            state["active_worktree"] = None
            save_state(state, root)
            print("✅ Worktree and task branch removed cleanly.")
            return 0
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to remove worktree: {e}")
            return 1

    elif action == "list":
        subprocess.run(["git", "worktree", "list"])
        return 0

# ---------------------------------------------------------------------------
# COMMAND: AUDIT (Zero-Trust Adversarial Diff Inspection)
# ---------------------------------------------------------------------------

FRAUD_PATTERNS = {
    "weakened_test_skip": (
        r"(\btest\.skip\b|\bxit\b|\bfit\b|\bfdescribe\b|\.only\(|\btest\.only\b|\bit\.only\b|\bdescribe\.only\b|@pytest\.mark\.skip|@pytest\.mark\.xfail|\bpytest\.xfail\b|\.skip\(|\bdescribe\.skip\b|(#|//)\s*(assert\b|expect\()|__import__\(['\"]pytest['\"]\)\.skip)",
        "Test skipped, disabled or commented out"
    ),
    "silent_failure_empty_catch": (
        r"(except(\s+[A-Za-z0-9_.]+(\s+as\s+\w+)?)?\s*:\s*(pass|\.\.\.)|catch\s*(\([^\)]*\))?\s*\{\s*\})",
        "Empty exception handler / Silent failure"
    ),
    "phantom_stub": (
        r"(def\s+\w+\s*\(.*\)\s*:\s*(pass|\.\.\.|return\s+None|return\s+\{\}|return\s+\[\]|return\s+['\"]['\"])|function\s+\w+\s*\(.*\)\s*\{\s*(return\s+null;|return\s+undefined;|return\s+\{\};)?\s*\}|throw\s+new\s+NotImplementedError)",
        "Stub or unfinished function body"
    ),
    "tautological_assertion": (
        r"^\s*(assert\s+(True|1\s*==\s*1|True\s*==\s*True|['\"][a-zA-Z0-9]+['\"]\s*==\s*['\"][a-zA-Z0-9]+['\"])|expect\((true|1)\)\.to(Be|Equal)\((true|1)\))",
        "Tautological or meaningless assertion (assert True / assert 1 == 1)"
    ),
    "obsolete_ai_model_reference": (r"(?i)\b(openai\s+codex|code-davinci-\d+|text-davinci-\d+|gpt-3\.5-turbo|gpt-4-0314|gpt-4-0613|gemini-1\.0|gemini-1\.5|claude-1\b|claude-2\b|claude-instant)\b", "Deprecated or obsolete AI model reference detected")
}

CODE_EXTENSIONS = (
    ".py", ".ts", ".js", ".jsx", ".tsx", ".java", ".go", ".rs", ".rb", ".php",
    ".cs", ".c", ".cpp", ".swift", ".kt", ".dart", ".sh", ".sql"
)
DOC_EXTENSIONS = (".md", ".txt", ".json", ".yaml", ".yml")
ALL_AUDIT_EXTENSIONS = CODE_EXTENSIONS + DOC_EXTENSIONS

def scan_diff_text(diff_text):
    """Robust algorithmic scanner for the 6 classic frauds across single and multi-line diff blocks."""
    violations = []
    lines = diff_text.splitlines()
    
    current_file = ""
    old_file = ""
    file_added_lines = {}
    file_deleted_asserts = {}
    file_added_asserts = {}
    file_deleted_tests = {}
    file_added_tests = {}

    for line in lines:
        if line.startswith("--- a/"):
            old_file = line[6:].strip()
            continue
        if line.startswith("+++ b/"):
            current_file = line[6:].strip()
            continue
        elif line.startswith("+++ /dev/null"):
            # Whole file was deleted
            current_file = old_file
            continue

        is_code = any(current_file.lower().endswith(ext) for ext in CODE_EXTENSIONS)
        is_doc = any(current_file.lower().endswith(ext) for ext in DOC_EXTENSIONS)
        if not (is_code or is_doc):
            continue

        if current_file not in file_added_lines:
            file_added_lines[current_file] = []
            file_deleted_asserts[current_file] = 0
            file_added_asserts[current_file] = 0
            file_deleted_tests[current_file] = 0
            file_added_tests[current_file] = 0

        if line.startswith("+") and not line.startswith("+++"):
            code_line = line[1:].rstrip()
            file_added_lines[current_file].append(code_line)
            # Count added assertions
            if is_code and re.search(r"^\s*(await\s+)?(assert\b|expect\(|self\.assert\w+|mock\.\w*assert)", code_line):
                file_added_asserts[current_file] += 1
            # Count added test functions
            if is_code and re.search(r"^\s*(def\s+test_\w+|it\s*\(|test\s*\()", code_line):
                file_added_tests[current_file] += 1

            # Single-line checks
            stripped_code = code_line.strip()
            # Skip embedded diff text fixtures inside test files (lines whose source text begins with '+')
            if stripped_code.startswith("+") or "FRAUD_PATTERNS" in stripped_code or "obsolete_ai_model_reference" in stripped_code:
                continue
            is_comment = stripped_code.startswith("#") or stripped_code.startswith("//") or stripped_code.startswith('"""') or stripped_code.startswith("'''") or stripped_code.startswith("*")
            for key, (pattern, desc) in FRAUD_PATTERNS.items():
                if not is_code and key != "obsolete_ai_model_reference":
                    continue
                if is_comment and key in ("silent_failure_empty_catch", "phantom_stub", "tautological_assertion"):
                    continue
                if is_comment and key == "weakened_test_skip" and not re.search(r"(#|//)\s*(assert\b|expect\()", stripped_code):
                    continue
                if re.search(pattern, stripped_code):
                    violations.append({
                        "file": current_file,
                        "line": stripped_code,
                        "fraud_type": key,
                        "description": desc
                    })

        elif line.startswith("-") and not line.startswith("---"):
            code_line = line[1:].rstrip()
            # Count deleted assertions
            if is_code and re.search(r"^\s*(await\s+)?(assert\b|expect\(|self\.assert\w+|mock\.\w*assert)", code_line):
                file_deleted_asserts[current_file] += 1
            # Count deleted test functions
            if is_code and re.search(r"^\s*(def\s+test_\w+|it\s*\(|test\s*\()", code_line):
                file_deleted_tests[current_file] += 1

    # Check for net assert deletions per file (prevents false positives on assert refactoring)
    for fname, del_count in file_deleted_asserts.items():
        add_count = file_added_asserts.get(fname, 0)
        if del_count > add_count:
            violations.append({
                "file": fname,
                "line": f"Deleted {del_count} assertions vs {add_count} added",
                "fraud_type": "assert_deletion",
                "description": f"Net assertion deletion detected ({del_count - add_count} assertions removed without replacement)"
            })

    # Check for net test function deletions per file
    for fname, del_t in file_deleted_tests.items():
        add_t = file_added_tests.get(fname, 0)
        if del_t > add_t:
            violations.append({
                "file": fname,
                "line": f"Deleted {del_t} test functions vs {add_t} added",
                "fraud_type": "weakened_test_skip",
                "description": f"Net test function deletion detected ({del_t - add_t} test functions deleted without replacement)"
            })

    # Multiline block scanner: comment-tolerant, whitespace-tolerant
    for fname, added in file_added_lines.items():
        n = len(added)
        for i in range(n):
            line_i = added[i].strip()

            # Python except block check
            if re.match(r"^except(\s+[A-Za-z0-9_.]+(\s+as\s+\w+)?)?\s*:", line_i):
                # Look ahead for first non-comment non-empty statement
                for j in range(i + 1, min(i + 10, n)):
                    next_stmt = added[j].strip()
                    if not next_stmt or next_stmt.startswith("#") or next_stmt.startswith('"""') or next_stmt.startswith("'''"):
                        continue
                    if re.match(r"^(pass|\.\.\.)\b", next_stmt):
                        violations.append({
                            "file": fname,
                            "line": f"{line_i} ... {next_stmt}",
                            "fraud_type": "silent_failure_empty_catch",
                            "description": "Multi-line empty exception handler (silent failure)"
                        })
                    break

            # JS/TS catch block check (matches both `catch (...) {` and `} catch (...) {`)
            if re.search(r"\bcatch(\s*\([^\)]*\))?\s*\{?", line_i):
                # Look ahead for next non-comment non-empty statement
                for j in range(i + 1, min(i + 10, n)):
                    next_stmt = added[j].strip()
                    if not next_stmt or next_stmt.startswith("//") or next_stmt.startswith("/*") or next_stmt.startswith("*"):
                        continue
                    if next_stmt == "}":
                        violations.append({
                            "file": fname,
                            "line": f"{line_i} ... }}",
                            "fraud_type": "silent_failure_empty_catch",
                            "description": "Multi-line empty catch block in JavaScript/TypeScript"
                        })
                    break

            # Function stub check (Python and JS/TS)
            is_py_func = re.match(r"^def\s+\w+\s*\(.*\)\s*:", line_i)
            is_js_func = re.match(r"^(function\s+\w+|const\s+\w+\s*=\s*(\([^\)]*\)|async\s*\([^\)]*\))\s*=>)\s*\{?", line_i)

            if is_py_func:
                for j in range(i + 1, min(i + 10, n)):
                    next_stmt = added[j].strip()
                    if not next_stmt or next_stmt.startswith("#") or next_stmt.startswith('"""') or next_stmt.startswith("'''"):
                        continue
                    if re.match(r"^(pass|\.\.\.|return\s+None|return\s+\{\}|return\s+\[\]|return\s+['\"]['\"])\b", next_stmt):
                        violations.append({
                            "file": fname,
                            "line": f"{line_i} ... {next_stmt}",
                            "fraud_type": "phantom_stub",
                            "description": f"Multi-line function stub ({next_stmt})"
                        })
                    break

            if is_js_func:
                for j in range(i + 1, min(i + 10, n)):
                    next_stmt = added[j].strip()
                    if not next_stmt or next_stmt.startswith("//") or next_stmt.startswith("/*") or next_stmt.startswith("*"):
                        continue
                    if next_stmt in ("}", "return null;", "return undefined;", "return {};", "return [];"):
                        violations.append({
                            "file": fname,
                            "line": f"{line_i} ... {next_stmt}",
                            "fraud_type": "phantom_stub",
                            "description": f"Multi-line function stub in JS/TS ({next_stmt})"
                        })
                    break

    return violations

def cmd_audit(args):
    root = find_repo_root()
    base_branch = args.base
    if not base_branch:
        check_main = subprocess.run(["git", "rev-parse", "--verify", "main"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=root)
        base_branch = "main" if check_main.returncode == 0 else "master"
    
    print(f"🔍 Running KAIROS Adversarial Zero-Trust Audit against '{base_branch}'...")

    diff_text = ""
    try:
        diff_res = subprocess.run(["git", "diff", f"{base_branch}...HEAD"],
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=root)
        if diff_res.returncode == 0:
            diff_text = diff_res.stdout
    except Exception:
        pass

    # Include unstaged / staged working tree diff as well
    local_diff = subprocess.run(["git", "diff", "HEAD"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=root)
    if local_diff.stdout.strip():
        diff_text += "\n" + local_diff.stdout
    
    if not diff_text.strip():
        unstaged = subprocess.run(["git", "diff"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=root)
        diff_text = unstaged.stdout

    if not diff_text.strip():
        print("ℹ️ Diff is empty. No changes detected to audit.")
        return 0

    violations = scan_diff_text(diff_text)

    print("=================================================================")
    print("🛡️  KAIROS ADVERSARIAL AUDIT REPORT")
    print("=================================================================")

    if not violations:
        state = load_state(root)
        state["current_stage"] = "VERIFIED"
        save_state(state, root)
        print("VERDICT: [ ✅ VERIFIED ]")
        print("• Zero fraudulent patterns detected.")
        print("• No weakened tests, empty catch blocks, or phantom stubs found.")
        print("=================================================================")
        return 0
    else:
        state = load_state(root)
        state["current_stage"] = "REPAIR_REQUIRED"
        save_state(state, root)
        print("VERDICT: [ ❌ REFUTED - FRAUD OR WEAKENED CHECKS DETECTED ]")
        print(f"Found {len(violations)} suspicious pattern(s):\n")
        for idx, v in enumerate(violations, 1):
            print(f" [{idx}] {v['description'].upper()}")
            print(f"     File: {v['file']}")
            print(f"     Line: {v['line']}")
        print("=================================================================")
        print("Action required: Resolve all violations before progressing to Ship.")
        return 1

# ---------------------------------------------------------------------------
# COMMAND: ARCHIVE (Promote Delta Spec to Living Spec)
# ---------------------------------------------------------------------------

def cmd_archive(args):
    root = find_repo_root()
    state = load_state(root)
    change_id = args.name or state.get("active_change")

    if not change_id:
        print("❌ No active change specified or found in state.")
        return 1

    k_dir = get_kairos_dir(root)
    change_dir = k_dir / "changes" / change_id
    specs_dir = k_dir / "specs"

    if not change_dir.exists():
        print(f"❌ Change directory not found: {change_dir}")
        return 1

    specs_file = change_dir / "specs.md"
    if specs_file.exists():
        target_spec = specs_dir / f"{change_id.split('_', 2)[-1]}.md"
        target_spec.write_text(specs_file.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"📜 Promoted living spec to: {target_spec.relative_to(root)}")

    # Mark archived in state
    state["history"].append({
        "change_id": change_id,
        "archived_at": datetime.now().isoformat(),
        "mode": state.get("mode")
    })
    state["active_change"] = None
    state["current_stage"] = "SHIPPED"
    save_state(state, root)

    print(f"✅ Change '{change_id}' successfully archived.")
    return 0

# ---------------------------------------------------------------------------
# COMMAND: EXPORT (Multi-Harness Adapter Generator)
# ---------------------------------------------------------------------------

def cmd_export(args):
    target = args.target.lower()
    root = find_repo_root()
    
    print(f"🚀 Exporting KAIROS configurations for harness: '{target}'...")

    if target in ["claude", "all"]:
        claude_dir = root / ".claude"
        claude_dir.mkdir(exist_ok=True)
        claude_md = root / "CLAUDE.md"
        claude_md.write_text("""# KAIROS Protocol for Claude Code
Always uphold the KAIROS Elastic Engine:
1. Assess complexity: Mode Alpha (UI/Lite), Mode Beta (Standard), Mode Gamma (Critical).
2. For Mode Alpha (<30 LOC / UI): Make surgical edits, run visual check, skip subagents.
3. For Mode Beta/Gamma: Never write production code without a failing test first (TDD).
4. Run adversarial check (`python3 scripts/kairos_cli.py audit`) before claiming done.
5. Zero tolerance for weakened assertions, phantom stubs, or silent failures.
""", encoding="utf-8")
        print("   ✅ Generated CLAUDE.md")

    if target in ["cursor", "all"]:
        cursor_dir = root / ".cursor" / "rules"
        cursor_dir.mkdir(parents=True, exist_ok=True)
        cursorrules = root / ".cursorrules"
        cursorrules.write_text("""# KAIROS Protocol for Cursor
- Apply the Elastic Dial: do not over-engineer simple UI changes.
- In logic and backend: TDD is mandatory (Red -> Green -> Refactor).
- Ground truth is `git diff`, never user or agent claims.
""", encoding="utf-8")
        print("   ✅ Generated .cursorrules and .cursor/rules/")

    if target in ["codex", "gemini", "universal", "windsurf", "openai", "agents", "all"]:
        agents_md = root / "AGENTS.md"
        agents_md.write_text("""# KAIROS Protocol for Autonomous Agents (Universal)
- Governed by KAIROS Adaptive SDLC.
- State tracked under `.kairos/state.json`.
- Delta specs organized under `.kairos/changes/`.
- Adversarial audits enforced via `kairos audit`.
""", encoding="utf-8")
        print("   ✅ Generated AGENTS.md")

    print(f"🎉 Multi-harness export completed successfully.")
    return 0

# ---------------------------------------------------------------------------
# COMMAND: UPDATE (Self-Update & Upstream Synchronization)
# ---------------------------------------------------------------------------

def cmd_update(args):
    root = find_repo_root()
    print("🔄 Checking for KAIROS framework updates from upstream...")
    
    # 1. Verify remote origin exists
    remotes = subprocess.run(["git", "remote"], capture_output=True, text=True, cwd=root)
    if "origin" not in remotes.stdout.split():
        print("⚠️ No 'origin' remote found. To set upstream:")
        print("   git remote add origin https://github.com/ismaelsoilet/kairos-framework.git")
        return 1

    try:
        # 2. Fetch updates
        print("📡 Fetching latest commits from origin/main...")
        subprocess.run(["git", "fetch", "origin", "main"], check=True, cwd=root, stdout=subprocess.DEVNULL)
        
        # 3. Check diff between HEAD and origin/main
        local_hash = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True, cwd=root).stdout.strip()
        remote_hash = subprocess.run(["git", "rev-parse", "origin/main"], capture_output=True, text=True, check=True, cwd=root).stdout.strip()
        
        if local_hash == remote_hash:
            print(f"✨ KAIROS is already up-to-date at commit {local_hash[:7]}.")
        else:
            print(f"📦 Upstream update found ({local_hash[:7]} -> {remote_hash[:7]}). Pulling changes...")
            subprocess.run(["git", "pull", "--ff-only", "origin", "main"], check=True, cwd=root)
            print("✅ Successfully updated local repository.")

        # 4. Sync to global plugin if installed in ~/.gemini/config/plugins/kairos
        global_plugin = Path.home() / ".gemini" / "config" / "plugins" / "kairos"
        if global_plugin.exists():
            for subfolder in ["scripts", "rules", "docs", "skills", "agents"]:
                src = root / subfolder
                dst = global_plugin / subfolder
                if src.exists():
                    shutil.copytree(src, dst, dirs_exist_ok=True)
            for fname in ["README.md", "README.pt-br.md"]:
                if (root / fname).exists():
                    shutil.copy2(root / fname, global_plugin / fname)
            print("🔗 Synced latest KAIROS rules and scripts to global plugin environment.")

        # 5. Run health self-test
        if not getattr(args, "skip_self_test", False):
            print("🧪 Running self-test suite to verify update integrity...")
            test_run = subprocess.run([sys.executable, "-m", "unittest", "tests/test_cli_features.py"],
                                      cwd=root, capture_output=True, text=True)
            if test_run.returncode == 0:
                print("🛡️  Self-test passed: 100% healthy.")
                return 0
            else:
                print("⚠️ Self-test reported issues after update:")
                print(test_run.stdout)
                return 1
        return 0
    except Exception as e:
        print(f"❌ Update failed: {e}")
        return 1

# ---------------------------------------------------------------------------
# COMMAND: REGISTRY (Agents & Skills Ecosystem)
# ---------------------------------------------------------------------------

def cmd_registry(args):
    root = find_repo_root()
    
    print("=================================================================")
    print("🧩 KAIROS AGENTS & SKILLS REGISTRY")
    print("=================================================================")

    # 1. Discover Agents
    agents = []
    agent_dirs = [root / "agents", root / ".kairos" / "agents"]
    for adir in agent_dirs:
        if adir.exists():
            for f in adir.glob("*.md"):
                content = f.read_text(encoding="utf-8")
                desc_match = re.search(r"description:\s*[\"']?([^\"'\n]+)", content)
                desc = desc_match.group(1) if desc_match else "Custom Agent"
                agents.append((f.stem, desc, str(f.relative_to(root))))

    # 2. Discover Skills
    skills = []
    skill_dirs = [root / "skills", root / ".kairos" / "skills"]
    for sdir in skill_dirs:
        if sdir.exists():
            for item in sdir.iterdir():
                if item.is_dir() and (item / "SKILL.md").exists():
                    content = (item / "SKILL.md").read_text(encoding="utf-8")
                    desc_match = re.search(r"description:\s*[\"']?([^\"'\n]+)", content)
                    desc = desc_match.group(1) if desc_match else "Agent Skill"
                    skills.append((item.name, desc, str(item.relative_to(root))))

    print("🤖 REGISTERED AGENT PERSONAS:")
    for name, desc, path in agents:
        print(f"  • {name:<22} ({path})")
        print(f"    └─ {desc[:80]}")

    print("\n⚡ REGISTERED SKILLS:")
    for name, desc, path in skills:
        print(f"  • {name:<22} ({path})")
        print(f"    └─ {desc[:80]}")

    print("-----------------------------------------------------------------")
    print("💡 Extension Guide:")
    print("  • To add an agent: create `agents/<name>.md` or `.kairos/agents/<name>.md`")
    print("  • To add a skill: create `skills/<name>/SKILL.md` or `.kairos/skills/<name>/SKILL.md`")
    print("  • KAIROS stages automatically load matching skills via the Elastic Dial.")
    print("=================================================================")
    return 0

# ---------------------------------------------------------------------------
# COMMAND: LESSON (In-Repo Continuous Learning)
# ---------------------------------------------------------------------------

def cmd_lesson(args):
    root = find_repo_root()
    lessons_file = root / ".kairos" / "lessons.md"

    if args.action == "list":
        if not lessons_file.exists():
            docs_lessons = root / "docs" / "AGENT_LESSONS.md"
            if docs_lessons.exists():
                print(f"📖 Showing KAIROS core lessons from {docs_lessons.relative_to(root)}:\n")
                print(docs_lessons.read_text(encoding="utf-8")[:1200] + "\n... [read docs/AGENT_LESSONS.md for full catalog]")
                return 0
            print("ℹ️ No lessons recorded yet in .kairos/lessons.md.")
            return 0
        print(f"📖 In-Repo Living Lessons ({lessons_file.relative_to(root)}):\n")
        print(lessons_file.read_text(encoding="utf-8"))
        return 0

    elif args.action == "add":
        if not args.title or not args.rule:
            print("❌ Both --title and --rule are required to add a lesson.")
            return 1
        
        lessons_file.parent.mkdir(parents=True, exist_ok=True)
        date_str = datetime.now().strftime("%Y-%m-%d")
        trap_line = f"* **The Trap:** {args.trap}\n" if getattr(args, "trap", None) else ""
        entry = f"\n## Lesson: {args.title} ({date_str})\n{trap_line}* **The KAIROS Directive:** {args.rule}\n"
        with open(lessons_file, "a", encoding="utf-8") as f:
            f.write(entry)
        print(f"✅ Lesson recorded in {lessons_file.relative_to(root)}: '{args.title}'")
        return 0
    return 0

# ---------------------------------------------------------------------------
# COMMAND: SCOUT (Technology Scout & Anti-Cutoff Reconnaissance)
# ---------------------------------------------------------------------------

HIGH_RISK_CUTOFF_PACKAGES = {
    "pydantic": "Breaking changes between v1 and v2 (.dict() removed, use .model_dump())",
    "next": "App Router vs Pages Router, async headers in v15",
    "react": "React 19 removals (forwardRef, useActionState, actions)",
    "vue": "Vue 2 Options API vs Vue 3 Composition API & script setup",
    "tailwind": "Tailwind v4 CSS-first config vs v3 tailwind.config.js",
    "tailwindcss": "Tailwind v4 CSS-first config vs v3 tailwind.config.js",
    "langchain": "Massive package split into langchain-core, langchain-community, 0.3+ imports",
    "openai": "SDK v1.0+ rewrite (client.chat.completions.create with current frontier models e.g. GPT-6 Astra, GPT-6.1 Sol, o4-mini; legacy GPT-4/3.5 endpoints removed)",
    "google-genai": "Modern Google GenAI SDK (google.genai.Client with current frontier models e.g. gemini-4-argon, gemini-3.8-flash) vs legacy google.generativeai",
    "@google/genai": "Modern Google GenAI SDK (@google/genai with current frontier models e.g. gemini-4-argon, gemini-3.8-flash) vs legacy @google/generative-ai",
    "flutter": "Material 3 defaults, Dart 3 pattern matching, accentColor removed",
    "fastapi": "Pydantic v2 integration, Lifespan handlers replacing on_event",
    "nestjs": "NestJS v10+ modern rxjs, express v5 compatibility",
    "astro": "Astro v4/v5 content layer and server islands",
    "vite": "Vite v5/v6 Rollup 4 adoption, SSR manifest updates",
    "colyseus": "Colyseus 0.15/0.16 breaking shifts: Schema v2, native reconnect tokens, matchMaker updates, built-in presence (do NOT reinvent state sync)",
    "@colyseus/schema": "Schema v2 binary serialization and filters (do NOT build custom delta serializers)"
}

def parse_project_dependencies(root: Path):
    """Scan and parse dependency manifests across multiple languages."""
    manifests_found = []
    deps = {}

    # 1. Node.js (package.json)
    pkg_json = root / "package.json"
    if pkg_json.exists():
        manifests_found.append("package.json")
        try:
            data = json.loads(pkg_json.read_text(encoding="utf-8"))
            for name, ver in {**data.get("dependencies", {}), **data.get("devDependencies", {})}.items():
                deps[name.lower()] = (name, str(ver), "package.json")
        except Exception:
            pass

    # 2. Python (pyproject.toml)
    pyproj = root / "pyproject.toml"
    if pyproj.exists():
        manifests_found.append("pyproject.toml")
        try:
            content = pyproj.read_text(encoding="utf-8")
            for m in re.finditer(r'["\']([a-zA-Z0-9_\-]+)\s*([=<>!~^]+[^"\']*)?["\']', content):
                name = m.group(1).lower()
                ver = m.group(2) or "any"
                if name not in deps:
                    deps[name] = (m.group(1), ver, "pyproject.toml")
        except Exception:
            pass

    # 3. Python (requirements.txt)
    reqs = root / "requirements.txt"
    if reqs.exists():
        manifests_found.append("requirements.txt")
        try:
            for line in reqs.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    m = re.match(r"^([a-zA-Z0-9_\-]+)([=<>!~]+.*)?$", line)
                    if m:
                        name = m.group(1).lower()
                        ver = m.group(2) or "any"
                        deps[name] = (m.group(1), ver, "requirements.txt")
        except Exception:
            pass

    # 4. Dart / Flutter (pubspec.yaml)
    pubspec = root / "pubspec.yaml"
    if pubspec.exists():
        manifests_found.append("pubspec.yaml")
        try:
            content = pubspec.read_text(encoding="utf-8")
            for line in content.splitlines():
                m = re.match(r"^\s{2}([a-zA-Z0-9_]+):\s*[\^~]?([0-9\.\-]+.*)?$", line)
                if m:
                    name = m.group(1).lower()
                    ver = m.group(2) or "any"
                    deps[name] = (m.group(1), ver, "pubspec.yaml")
        except Exception:
            pass

    # 5. Rust (Cargo.toml)
    cargo = root / "Cargo.toml"
    if cargo.exists():
        manifests_found.append("Cargo.toml")
        try:
            content = cargo.read_text(encoding="utf-8")
            for m in re.finditer(r'([a-zA-Z0-9_\-]+)\s*=\s*["\']([^"\']+)["\']', content):
                name = m.group(1).lower()
                ver = m.group(2)
                deps[name] = (m.group(1), ver, "Cargo.toml")
        except Exception:
            pass

    # 6. Go (go.mod)
    gomod = root / "go.mod"
    if gomod.exists():
        manifests_found.append("go.mod")
        try:
            content = gomod.read_text(encoding="utf-8")
            for m in re.finditer(r'([a-zA-Z0-9_\-\./]+)\s+v([0-9\.\-]+)', content):
                name = m.group(1).split("/")[-1].lower()
                ver = "v" + m.group(2)
                deps[name] = (m.group(1), ver, "go.mod")
        except Exception:
            pass

    return manifests_found, deps

def cmd_scout(args):
    root = find_repo_root()
    manifests, deps = parse_project_dependencies(root)

    print("=================================================================")
    print("🔭 KAIROS SCOUT: TECH STACK & ANTI-CUTOFF RECONNAISSANCE")
    print("=================================================================")

    if not manifests:
        print("ℹ️ No standard dependency manifests detected in project root.")
        print("   (Checked package.json, pyproject.toml, requirements.txt, pubspec.yaml, Cargo.toml, go.mod)")
        return 0

    print(f"📦 Manifests detected: {', '.join(manifests)}")
    print(f"📊 Total dependencies indexed: {len(deps)}\n")

    cutoff_risks = []
    for key, (orig_name, ver, manifest) in deps.items():
        if key in HIGH_RISK_CUTOFF_PACKAGES:
            cutoff_risks.append((orig_name, ver, manifest, HIGH_RISK_CUTOFF_PACKAGES[key]))

    if cutoff_risks:
        print("🚨 HIGH KNOWLEDGE-CUTOFF RISKS DETECTED:")
        print("-----------------------------------------------------------------")
        for name, ver, manifest, advice in cutoff_risks:
            print(f"  ⚠️  {name} ({ver}) [from {manifest}]")
            print(f"     └─ Risk: {advice}")
        print("-----------------------------------------------------------------")
        print("💡 Directive for Agent:")
        print("   • Do NOT guess APIs for these packages based on training weights!")
        print("   • Run `kairos_scout` or verify method signatures in local types / live docs.")
    else:
        print("✅ No known high-risk knowledge cutoff libraries flagged.")

    if getattr(args, "all", False):
        print("\n📋 All Indexed Dependencies:")
        for name, ver, manifest in sorted(deps.values(), key=lambda x: x[0].lower()):
            print(f"  • {name:<25} {ver:<15} ({manifest})")

    if getattr(args, "save_spec", False):
        k_dir = get_kairos_dir(root)
        changes_dir = k_dir / "changes"
        if changes_dir.exists():
            active_changes = sorted([d for d in changes_dir.iterdir() if d.is_dir()], reverse=True)
            if active_changes:
                target_change = active_changes[0]
                research_file = target_change / "research.md"
                content = f"""# KAIROS Research Brief: {target_change.name}
Generated by `kairos scout` on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Manifest Reconnaissance
* **Manifests Found:** {', '.join(manifests)}
* **Total Packages:** {len(deps)}

## High-Risk Knowledge Cutoff Packages
"""
                if cutoff_risks:
                    for name, ver, manifest, advice in cutoff_risks:
                        content += f"- **{name}** (`{ver}` in `{manifest}`): {advice}\n"
                else:
                    content += "No high-risk cutoff libraries flagged.\n"

                content += """
## Pre-Brainstorming Stack Discovery (Native Primitives First)
- **Rule of Minimal Surface:** Before brainstorming custom logic or complex architectures, inspect if the modern framework release already provides native primitives (e.g. built-in state sync, reconnect tokens, schema serialization, automated routers).
- **Zero Reinvented Wheels:** If the installed framework version solves the problem natively, brainstorming MUST adopt the native feature instead of specifying custom workarounds.

## Negative Directives for Brainstorming & Worker
- Do NOT brainstorm or specify custom workarounds for problems already resolved in modern releases.
- Do NOT guess deprecated methods from training memory.
- Verify live docs or local type definitions before declaring external API contracts.
"""
                research_file.write_text(content, encoding="utf-8")
                print(f"\n📝 Research brief saved to: {research_file.relative_to(root)}")

    print("=================================================================")
    return 0

# ---------------------------------------------------------------------------
# COMMAND: STATUS & TELEMETRY
# ---------------------------------------------------------------------------

def cmd_status(args):
    root = find_repo_root()
    state = load_state(root)
    stage = state.get("current_stage", "IDLE")
    mode = state.get("mode", "alpha").upper()
    budget = state.get("token_budget", 15000)
    consumed = state.get("total_tokens_consumed", 0)
    remaining = max(0, budget - consumed)
    pct_used = (consumed / budget * 100) if budget > 0 else 0
    change = state.get("active_change") or "None"
    worktree = state.get("active_worktree") or "None (In-place)"

    header = f"⚡ [KAIROS | Stage: {stage} | Mode: {mode} | Tokens: {consumed:,}/{budget:,} ({pct_used:.1f}%) | Left: {remaining:,}]"

    if getattr(args, "header_only", False):
        print(header)
        return 0

    if getattr(args, "dashboard", False):
        stages = ["IDLE", "CLASSIFIED", "RESEARCHING", "BRAINSTORMING", "SPECIFYING", "BUILDING", "AUDITING", "VERIFIED", "SHIPPED"]
        current_idx = stages.index(stage) if stage in stages else 0
        stage_pct = int(((current_idx + 1) / len(stages)) * 100)

        filled_stages = int((current_idx + 1) / len(stages) * 14)
        stage_bar = "█" * filled_stages + "░" * (14 - filled_stages)

        token_ratio = min(1.0, consumed / budget) if budget > 0 else 0
        filled_tok = int(token_ratio * 14)
        tok_bar = "█" * filled_tok + "░" * (14 - filled_tok)

        print("\n┌──────────────────────────────────────────────────────────────┐")
        print(f"│ 🧭 KAIROS MISSION CONTROL DASHBOARD                         │")
        print("├──────────────────────────────────────────────────────────────┤")
        print(f"│ Stage: [{stage_bar}] {stage_pct:>3}%  ({stage:<10})      │")
        print(f"│ Token: [{tok_bar}] {pct_used:>5.1f}% ({consumed:,}/{budget:,} tok) │")
        print(f"│ Mode:  MODE {mode:<7}  Worktree: {Path(worktree).name:<18}    │")
        print(f"│ Change: {change[:48]:<52} │")
        print("└──────────────────────────────────────────────────────────────┘\n")
        return 0

    print("=================================================================")
    print("🧭 KAIROS REAL-TIME TELEMETRY & STAGE STATUS")
    print("=================================================================")
    print(header)
    print("-----------------------------------------------------------------")
    print(f"• Current Stage:     {stage}")
    print(f"• Active Mode:       MODE {mode}")
    print(f"• Active Change ID:  {change}")
    print(f"• Active Worktree:   {worktree}")
    print(f"• Tokens Consumed:   {consumed:,} tokens")
    print(f"• Token Budget Cap:  {budget:,} tokens")
    print(f"• Remaining Budget:  {remaining:,} tokens ({100 - pct_used:.1f}% remaining)")
    print("=================================================================")
    return 0

def cmd_token(args):
    root = find_repo_root()
    state = load_state(root)
    action = args.action
    if action == "add":
        if args.count <= 0:
            raise ValueError(f"Token count must be a positive integer, got: {args.count}")
        state["total_tokens_consumed"] = state.get("total_tokens_consumed", 0) + args.count
        save_state(state, root)
        print(f"✅ Added {args.count:,} tokens. Total consumed: {state['total_tokens_consumed']:,} tokens.")
    elif action == "reset":
        state["total_tokens_consumed"] = 0
        save_state(state, root)
        print("✅ Token counter reset to 0.")
    elif action == "set-stage":
        state["current_stage"] = args.stage.upper()
        save_state(state, root)
        print(f"✅ Current stage updated to: {state['current_stage']}")
    return 0

# ---------------------------------------------------------------------------
# COMMAND: ROLLBACK
# ---------------------------------------------------------------------------

def cmd_rollback(args=None):
    root = find_repo_root()
    state = load_state(root)
    print("⚠️ Initiating KAIROS Worktree Rollback (Discarding dirty state)...")
    try:
        # Safety backup of uncommitted changes before destructive reset
        diff_res = subprocess.run(["git", "diff", "HEAD"], stdout=subprocess.PIPE, text=True)
        if diff_res.stdout.strip():
            backup_patch = get_kairos_dir(root) / f"rollback_backup_{int(datetime.now().timestamp())}.patch"
            backup_patch.write_text(diff_res.stdout, encoding="utf-8")
            print(f"📦 Safety backup of uncommitted changes saved to: {backup_patch.relative_to(root)}")

        subprocess.run(["git", "reset", "--hard", "HEAD"], check=True)
        subprocess.run(["git", "clean", "-fd"], check=True)
        state["current_stage"] = "ROLLED_BACK"
        save_state(state, root)
        print("✅ Worktree restored to clean HEAD snapshot.")
        return 0
    except Exception as e:
        print(f"❌ Rollback failed: {e}")
        return 1

# ---------------------------------------------------------------------------
# COMMAND: MUTATE (K-Mutant Mutation Testing Engine)
# ---------------------------------------------------------------------------

MUTATION_OPS = [
    (r"(?<![!=<>])==(?!=)", "!="),
    (r"!=", "=="),
    (r"===", "!=="),
    (r"!==", "==="),
    (r">=", "<"),
    (r"<=", ">"),
    (r"&&", "||"),
    (r"\|\|", "&&"),
    (r"(?<!\+)\+(?!\+)", "-"),
    (r"(?<!\-)\-(?!\-)", "+"),
    (r"\bTrue\b", "False"),
    (r"\bFalse\b", "True"),
    (r"\btrue\b", "false"),
    (r"\bfalse\b", "true"),
    (r"\breturn True\b", "return False"),
    (r"\breturn False\b", "return True"),
    (r"\breturn true\b", "return false"),
    (r"\breturn false\b", "return true"),
]

def cmd_mutate(args):
    target_path = Path(args.target).resolve()
    if not target_path.exists():
        print(f"❌ Target file not found: {target_path}")
        return 1

    bak_path = target_path.with_suffix(target_path.suffix + ".kairos_bak")
    if bak_path.exists():
        # Recovery from previous interrupted run
        shutil.copy2(bak_path, target_path)
        bak_path.unlink()

    test_cmd = args.test
    max_mutants = getattr(args, "max_mutants", 10) or 10
    timeout_sec = getattr(args, "timeout", 15) or 15

    original_content = target_path.read_text(encoding="utf-8")
    shutil.copy2(target_path, bak_path)
    mutations_generated = []

    lines = original_content.splitlines(keepends=True)
    in_docstring = False
    for line_idx, line in enumerate(lines):
        stripped = line.strip()
        if '"""' in stripped or "'''" in stripped:
            if stripped.count('"""') == 1 or stripped.count("'''") == 1:
                in_docstring = not in_docstring
            continue
        if in_docstring or stripped.startswith("#"):
            continue

        for pattern, replacement in MUTATION_OPS:
            if re.search(pattern, line):
                new_line = re.sub(pattern, replacement, line, count=1)
                mutant_lines = list(lines)
                mutant_lines[line_idx] = new_line
                mutations_generated.append(("".join(mutant_lines), f"Line {line_idx+1}: {pattern} -> {replacement}"))
                if len(mutations_generated) >= max_mutants:
                    break
        if len(mutations_generated) >= max_mutants:
            break

    if not mutations_generated:
        if bak_path.exists():
            bak_path.unlink()
        print("ℹ️ No mutatable operators found in target file.")
        return 0

    print("=================================================================")
    print(f"🧬 KAIROS K-MUTANT ENGINE: MUTATION TESTING FOR [{target_path.name}]")
    print("=================================================================")
    print(f"• Generated Mutants: {len(mutations_generated)}")
    print(f"• Test Command:     {test_cmd}")
    print(f"• Timeout per Run:  {timeout_sec}s\n")

    killed = 0
    survived = 0

    try:
        for idx, (mutant_content, desc) in enumerate(mutations_generated, 1):
            target_path.write_text(mutant_content, encoding="utf-8")
            try:
                res = subprocess.run(test_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=timeout_sec)
                if res.returncode != 0:
                    killed += 1
                    print(f"  [{idx}/{len(mutations_generated)}] 💀 KILLED:   {desc}")
                else:
                    survived += 1
                    print(f"  [{idx}/{len(mutations_generated)}] ⚠️  SURVIVED: {desc} (Weak Test!)")
            except subprocess.TimeoutExpired:
                killed += 1
                print(f"  [{idx}/{len(mutations_generated)}] 💀 KILLED (TIMEOUT): {desc}")
    finally:
        if bak_path.exists():
            shutil.copy2(bak_path, target_path)
            bak_path.unlink()
        else:
            target_path.write_text(original_content, encoding="utf-8")

    score = (killed / len(mutations_generated) * 100) if mutations_generated else 100
    print("-----------------------------------------------------------------")
    print(f"🎯 MUTATION SCORE: {score:.1f}% (Killed: {killed} | Survived: {survived})")
    print(f"🛡️  Source file [{target_path.name}] successfully restored.")
    print("=================================================================")
    return 0 if survived == 0 else 1

# ---------------------------------------------------------------------------
# MAIN CLI DISPATCHER
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(prog="kairos", description="KAIROS: Adaptive SDLC & Token Governance CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Init
    subparsers.add_parser("init", help="Initialize KAIROS in the current project")

    # Dial
    p_dial = subparsers.add_parser("dial", help="Classify task complexity (The Elastic Dial)")
    p_dial.add_argument("description", nargs="+", help="Description of the task to classify")
    p_dial.add_argument("--force-gamma", action="store_true", help="Force Gamma mode (Critical)")
    p_dial.add_argument("--force-beta", action="store_true", help="Force Beta mode (Standard)")

    # Spec
    p_spec = subparsers.add_parser("spec", help="Scaffold a Delta Spec in .kairos/changes/")
    p_spec.add_argument("name", help="Short name of the feature or change")

    # Worktree
    p_wt = subparsers.add_parser("worktree", help="Manage isolated git worktrees")
    p_wt.add_argument("action", choices=["create", "remove", "list"], help="Worktree action")
    p_wt.add_argument("name", nargs="?", default=None, help="Name of the worktree branch")

    # Audit
    p_audit = subparsers.add_parser("audit", help="Adversarially audit git diff for the 6 classic frauds")
    p_audit.add_argument("--base", default="main", help="Base branch to diff against (default: main)")

    # Archive
    p_arc = subparsers.add_parser("archive", help="Promote Delta Spec to living specs")
    p_arc.add_argument("name", nargs="?", default=None, help="Change ID to archive")

    # Export
    p_exp = subparsers.add_parser("export", help="Export KAIROS configuration to other harnesses")
    p_exp.add_argument("target", choices=["claude", "cursor", "codex", "gemini", "windsurf", "openai", "agents", "universal", "all"], help="Target harness")

    # Status & Telemetry
    p_stat = subparsers.add_parser("status", help="Show current stage and token telemetry")
    p_stat.add_argument("--header-only", action="store_true", help="Print only the single-line telemetry header")
    p_stat.add_argument("--dashboard", action="store_true", help="Display visual terminal mission control dashboard")

    # Token management
    p_tok = subparsers.add_parser("token", help="Manage token budget and telemetry")
    p_tok.add_argument("action", choices=["add", "reset", "set-stage"], help="Token action")
    p_tok.add_argument("count", nargs="?", type=int, default=0, help="Tokens to add")
    p_tok.add_argument("--stage", default="IDLE", help="Stage name for set-stage")

    # Rollback
    subparsers.add_parser("rollback", help="Safely discard dirty state in worktree")

    # Mutate
    p_mut = subparsers.add_parser("mutate", help="Run K-Mutant Mutation Testing on target file")
    p_mut.add_argument("target", help="Target source file to mutate")
    p_mut.add_argument("--test", required=True, help="Test command to run for each mutant")
    p_mut.add_argument("--max-mutants", type=int, default=10, help="Max mutants to test")
    p_mut.add_argument("--timeout", type=int, default=15, help="Timeout in seconds per mutant run (prevents infinite loop hang)")

    # Update
    p_upd = subparsers.add_parser("update", help="Update KAIROS CLI and rules from upstream repository")
    p_upd.add_argument("--skip-self-test", action="store_true", help="Skip running test suite after update")

    # Registry
    subparsers.add_parser("registry", help="Discover and list registered agents and skills")

    # Lesson
    p_les = subparsers.add_parser("lesson", help="Manage in-repo continuous learning lessons (.kairos/lessons.md)")
    p_les.add_argument("action", choices=["list", "add"], help="Lesson action (list, add)")
    p_les.add_argument("--title", help="Lesson title")
    p_les.add_argument("--trap", help="Trap or failure mode description")
    p_les.add_argument("--rule", help="KAIROS directive or preventive rule")

    # Scout
    p_scout = subparsers.add_parser("scout", help="Inspect tech stack manifests, detect knowledge cutoff risks, and scaffold research.md")
    p_scout.add_argument("--all", action="store_true", help="Display all indexed dependencies")
    p_scout.add_argument("--save-spec", action="store_true", help="Save research findings to active Delta Spec's research.md")

    args = parser.parse_args()

    dispatch = {
        "init": cmd_init,
        "dial": cmd_dial,
        "spec": cmd_spec,
        "worktree": cmd_worktree,
        "audit": cmd_audit,
        "archive": cmd_archive,
        "export": cmd_export,
        "status": cmd_status,
        "token": cmd_token,
        "rollback": cmd_rollback,
        "mutate": cmd_mutate,
        "update": cmd_update,
        "registry": cmd_registry,
        "lesson": cmd_lesson,
        "scout": cmd_scout,
    }

    try:
        exit_code = dispatch[args.command](args)
        sys.exit(exit_code or 0)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
