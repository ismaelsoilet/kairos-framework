#!/usr/bin/env python3
"""
KAIROS CLI: the checks a coding agent cannot do for itself.

Four commands, one cycle:

    fit         should this ticket have a spec at all?
    brainstorm  alternatives and falsification before committing to one design
    gate        does the delivered diff match the approved spec, and do the tests run?
    audit       scan a diff for the fraud patterns that actually hold up

Everything else this CLI used to carry — an Elastic Dial, four agent personas,
nine lifecycle stages, worktrees, mutation testing, exports, a registry, lessons,
a self-update engine — was removed in v1.3. None of it had evidence behind it,
and the classifier in particular made decisions it could not justify. What
remains is what survived measurement; the record is in docs/EVIDENCE.md.

Zero dependencies. Python 3.10+.
"""

import sys
import os
import json
import re
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

try:
    import fcntl
except ImportError:
    fcntl = None

VERSION = "1.3.0"

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

import threading

_state_thread_lock = threading.RLock()
_state_lock_depth = 0
_state_lock_fd = None

class StateLock:
    """Reentrant inter-process & inter-thread lock protecting .kairos/state.json against race conditions."""
    def __init__(self, k_dir):
        self.k_dir = k_dir

    def __enter__(self):
        global _state_lock_depth, _state_lock_fd
        _state_thread_lock.acquire()
        if _state_lock_depth == 0:
            if fcntl is not None:
                try:
                    lock_file = self.k_dir / ".state.lock"
                    lock_file.parent.mkdir(parents=True, exist_ok=True)
                    _state_lock_fd = open(lock_file, "a+", encoding="utf-8")
                    fcntl.flock(_state_lock_fd.fileno(), fcntl.LOCK_EX)
                except (OSError, IOError):
                    _state_lock_fd = None
        _state_lock_depth += 1
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        global _state_lock_depth, _state_lock_fd
        _state_lock_depth -= 1
        if _state_lock_depth == 0:
            if fcntl is not None and _state_lock_fd is not None:
                try:
                    fcntl.flock(_state_lock_fd.fileno(), fcntl.LOCK_UN)
                except (OSError, IOError) as err:
                    _flock_err = str(err)
                try:
                    _state_lock_fd.close()
                except (OSError, IOError) as err:
                    _close_err = str(err)
                _state_lock_fd = None
        _state_thread_lock.release()

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
        with StateLock(k_dir):
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
    with StateLock(k_dir):
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp_file, state_file)

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

SPECS_TEMPLATE = """# Specification: {name}
* **Change ID:** {change_id}

> Generated by `kairos spec`. The eight sections below are the checklist measured
> in the Uvik SDD Benchmark 2026: specs covering 6 or more merged 89.3% of the
> time, fewer merged 60.0%. Delete a section only if it genuinely does not apply,
> and say why in one line — `kairos gate` counts them.

## Goal
<!-- One sentence: the outcome for the user or the system. -->

## Scope
<!-- What is in scope, and what is explicitly out of scope. -->
- In scope:
- Out of scope:

## Inputs and outputs
<!-- Data in, data out, with types. Include the interface or API surface. -->

## Data changes
<!-- Schema, migrations, contracts. Write "None" if there are none. -->

## Edge cases
<!-- Error behaviour and unusual input. -->

## Acceptance tests
<!-- Bulleted and checkable. Each item should be provable by a test. -->
- [ ] 

## Constraints
<!-- Performance, security, compatibility, dependencies. -->

## No-change list
<!-- Files, interfaces or behaviours that MUST NOT change. The gate blocks on these. -->
- 

## Detailed implementation plan
<!-- Every file that will be created, changed or deleted, with a rationale.
     `kairos gate` compares this list with the diff and reports scope drift. -->
- `path/to/file` — what changes and why

## Invariants (must never break)
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
    print(f"\n💡 Next step: fill the sections, then `kairos gate --spec <path> --base main`")
    return 0

FRAUD_PATTERNS = {
    "weakened_test_skip": (
        r"((?<!\.)\b(xit|fit|fdescribe)\s*\(|\b(describe|it|test|context)\.(only|skip)\s*\(|@pytest\.mark\.(skip|xfail)|\bpytest\.(xfail|skip)\b|@unittest\.skip\b|\bunittest\.skip\b|\braise\s+(unittest\.)?SkipTest\b|(#|//)\s*(assert\b|expect\()|__import__\(['\"]pytest['\"]\)\.skip)",
        "Test skipped, disabled or commented out"
    ),
    "silent_failure_empty_catch": (
        r"(except(\s+[A-Za-z0-9_.]+(\s+as\s+\w+)?)?\s*:\s*(pass|\.\.\.|None|return|continue|0|1|False|True|''|\"\"|\{\})\b|catch\s*(\([^\)]*\))?\s*\{\s*(void\s+0;?|;|return;?|return\s+null;?|return\s+undefined;?)?\s*\})",
        "Empty exception handler / Silent failure"
    ),
    "phantom_stub": (
        r"(^\s*def\s+\w+\s*\(.*\)\s*:\s*(pass|\.\.\.|return\s+None|return\s+\{\}|return\s+\[\]|return\s+['\"]['\"])|^\s*(?:export\s+)?(?:async\s+)?function\s+\w+\s*\([^)]*\)\s*\{\s*(return\s+(null|undefined|\{\}|\[\]);?)?\s*\}|throw\s+new\s+NotImplementedError|raise\s+NotImplementedError)",
        "Stub or unfinished function body"
    ),
    "tautological_assertion": (
        r"^\s*(assert\s+(True|False|1\s*==\s*1|2\s*==\s*2|0\s*==\s*0|True\s*==\s*True|True\s+is\s+True|not\s+False|bool\s*\(1\)|['\"][a-zA-Z0-9]+['\"]\s*==\s*['\"][a-zA-Z0-9]+['\"])|expect\((true|false|1|2)\)\.to(Be|Equal)\((true|false|1|2)\)|expect\((true|1)\)\.toBeTruthy\(\))",
        "Tautological or meaningless assertion (e.g. assert True / assert 1 == 1 / assert 2 == 2 / expect(true).toBeTruthy())"
    ),
    "obsolete_ai_model_reference": (r"(?i)\b(openai\s+codex|code-davinci-\d+|text-davinci-\d+|gpt-3\.5-turbo|gpt-4-0314|gpt-4-0613|gemini-1\.0|gemini-1\.5|claude-1\b|claude-2\b|claude-instant)\b", "Deprecated or obsolete AI model reference detected")
}

CODE_EXTENSIONS = (
    ".py", ".ts", ".js", ".jsx", ".tsx", ".java", ".go", ".rs", ".rb", ".php",
    ".cs", ".c", ".cpp", ".swift", ".kt", ".dart", ".sh", ".sql"
)
DOC_EXTENSIONS = (".md", ".txt", ".json", ".yaml", ".yml")
ALL_AUDIT_EXTENSIONS = CODE_EXTENSIONS + DOC_EXTENSIONS

MUTATION_OPS = [
    (r"===", "!=="),
    (r"!==(?![\=])", "==="),
    (r"(?<![!=<>])==(?!=)", "!="),
    (r"(?<!\!)!=(?!=)", "=="),
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

def is_test_file(path_str: str) -> bool:
    """Strictly identify whether a path points to test files or test suites."""
    path_lower = path_str.lower().replace("\\", "/")
    parts = path_lower.split("/")
    filename = parts[-1]
    is_in_test_dir = any(p in ("tests", "test", "__tests__", "spec", "specs") for p in parts[:-1])
    is_test_filename = (
        filename.startswith("test_") or
        filename.endswith("_test.py") or
        filename.endswith(".test.ts") or
        filename.endswith(".spec.ts") or
        filename.endswith(".test.js") or
        filename.endswith(".spec.js") or
        filename.endswith("_test.go") or
        filename.endswith("_test.dart") or
        filename.endswith("test.py")
    )
    return is_in_test_dir or is_test_filename

ASSERT_LINE_RE = re.compile(r"^\s*(await\s+)?(assert\b|self\.assert\w+\(|expect\()")
# `with pytest.raises(...)` / `assertRaises` are assertions about behaviour, and
# usually replace a weaker try/except+assert pattern. Counting them as zero made
# the deletion detector fire on a strict improvement.
RAISES_LINE_RE = re.compile(r"\bwith\s+(pytest|self)\.raises\s*\(|\bassertRaises\b|\bexpect\s*\(.*\)\s*\.toThrow")
GUARD_LINE_RE = re.compile(r"^\s*(if|unless)\b")
REJECT_STMT_RE = re.compile(r"\b(raise|throw|return\s+(False|false|None|null|undefined|res\.status\(4)|continue|break|abort|deny)\b|status\(\s*4\d\d\s*\)")
MOCK_PATCH_RE = re.compile(
    r"^\s*[A-Za-z_]\w*\.[A-Za-z_]\w*\s*=\s*(MagicMock|Mock|mocker\.Mock|jest\.fn|vi\.fn|unittest\.mock\.Mock)\s*\("
)
MOCK_SPY_RE = re.compile(
    r"\b(jest|vi)\.spyOn\s*\([^)]*\)\s*\.\s*mock(ReturnValue|Implementation|ResolvedValue|ReturnValueOnce)\s*\("
)
GUARD_BOUNDARY_RE = re.compile(r"(<=|>=|<|>)\s*(-?\d+(?:\.\d+)?)")

# A guard that rejects fewer inputs than before is weaker. `<=` is stricter than `<`;
# `>=` is stricter than `>`.
STRICTER = {"<": "<=", ">": ">="}

def _count_guards(lines):
    """Count validation branches, including guards split across two lines."""
    count = 0
    for idx, raw in enumerate(lines):
        if not GUARD_LINE_RE.match(raw):
            continue
        if REJECT_STMT_RE.search(raw):
            count += 1
            continue
        # Guard whose rejection sits on the following line (Python style).
        for nxt in lines[idx + 1: idx + 3]:
            if not nxt.strip():
                continue
            if REJECT_STMT_RE.search(nxt):
                count += 1
            break
    return count

def _assert_expression(line):
    """Extract the boolean expression of a Python assert or jest/vitest expect(...) call."""
    m = re.search(r"\bassert\b\s*(.*)$", line)
    if m:
        expr = m.group(1)
    else:
        m = re.search(r"expect\s*\(([^)]*)\)", line)
        if not m:
            return None
        expr = m.group(1)
    expr = re.split(r"\s+#", expr)[0].strip().rstrip(";")
    return expr or None

def _assert_strength(line):
    """Classify an assertion as 'strong', 'weak', or None if it is not an assertion.

    strong = compares against a concrete value or type
    weak   = only checks existence / truthiness, which accepts almost anything
    """
    expr = _assert_expression(line)
    if expr is None:
        return None
    # Jest/Vitest existence matchers verify presence, not value.
    if re.search(r"\.(toBeDefined|toBeTruthy|toBeFalsy|toBeNull|toBeUndefined)\s*\(", line):
        return "weak"
    # Jest/Vitest value matchers with a concrete literal are strong.
    if re.search(r"\.(toBe|toEqual|toStrictEqual|toMatchObject|toContain)\s*\(\s*['\"\-\d\[]", line):
        return "strong"
    # Jest/Vitest value matchers with a variable argument still compare values.
    if re.search(r"\.(toBe|toEqual|toStrictEqual|toMatchObject|toContain)\s*\(\s*[A-Za-z_$]", line):
        return "strong"
    if re.search(r"\bis\s+not\s+None\b|\bis\s+None\b|!==\s*null|===\s*null", expr):
        return "weak"
    if re.search(r"==|!=|>=|<=|<=>|\bin\b|\bis\b|\binstanceof\b|\btypeof\b", expr):
        return "strong"
    if re.match(r"^(not\s+)?[A-Za-z_][\w\.\[\]'\"]*$", expr):
        return "weak"
    return "strong"

def _is_success_return(stmt):
    """True when a handler returns something that reports success or absence."""
    s = stmt.strip().rstrip(";")
    if re.match(r"^return\s+(True|true|1|200)\b", s):
        return True
    if re.match(r"^return\s+(None|null|undefined|0|\[\]|\{\})\s*$", s):
        return True
    if re.search(r"^return\s*\{.*['\"]?(ok|success|allowed)['\"]?\s*:\s*(True|true)", s):
        return True
    return False

def _judge_handler(body, fname, header, language, violations, context_lines=None):
    """Judge an exception handler body: swallows-and-succeeds vs legitimate handling.

    `context_lines` is the surrounding added block. It lets the judge tell a
    deliberate retry (`continue` inside a loop introduced in the same diff) from
    a swallow.
    """
    meaningful = [b for b in body if b.strip() and not b.strip().startswith(("#", "//", "*", "/*"))]
    if not meaningful:
        violations.append({
            "file": fname,
            "line": header,
            "fraud_type": "silent_failure_empty_catch",
            "description": "Empty exception handler (silent failure)"
        })
        return
    # A handler that re-raises or re-throws is doing its job.
    if any(re.match(r"^(raise|throw)\b", b) or re.search(r"\bthrow\s+(new\s+)?\w", b) for b in meaningful):
        return
    first = meaningful[0]
    in_retry_loop = bool(context_lines) and any(
        re.match(r"^\s*(for|while)\b", c) for c in (context_lines or [])
    )
    if first == "continue" and in_retry_loop:
        return
    if (re.match(r"^(pass|\.\.\.|continue|return|void\s+0)\s*;?\s*$", first)
            or first in ("0", "1", "False", "True", "''", '""', "{}", ";", "None")):
        violations.append({
            "file": fname,
            "line": f"{header} ... {first}",
            "fraud_type": "silent_failure_empty_catch",
            "description": "Empty exception handler (silent failure)"
        })
        return
    for stmt in meaningful:
        if _is_success_return(stmt):
            violations.append({
                "file": fname,
                "line": f"{header} ... {stmt}",
                "fraud_type": "silent_failure_empty_catch",
                "description": "Handler swallows the error and returns success/absence instead of propagating"
            })
            return

def _strip_string_context(added_lines):
    """Mark added-line indices that sit inside a multi-line string literal.

    Real diffs embed code in triple-quoted fixtures — e.g.
    `testdir.getitem("def test_x(): pass")` in pytest's own suite, or template
    strings in JS. Matching inside those was the single largest source of false
    positives in the external study (17 of 38 flags).
    """
    inside = set()
    open_delim = None
    for idx, line in enumerate(added_lines):
        if open_delim is not None:
            inside.add(idx)
            if line.count(open_delim) % 2 == 1:
                open_delim = None
            continue
        # A line that opens a block string is itself code; lines after it are not.
        for delim in ('"""', "'''", "`"):
            if line.count(delim) % 2 == 1:
                open_delim = delim
                break
    return inside

_INLINE_STRING_RE = re.compile(r"""('(?:\\.|[^'\\])*'|"(?:\\.|[^"\\])*"|`(?:\\.|[^`\\])*`)""")

def _strip_inline_strings(line):
    """Replace the contents of single-line string literals with empty strings.

    Code passed as data (`testdir.getitem("def test_x(): pass")`, template
    snippets, generated fixtures) must not be judged as if it were code.
    """
    if '"' not in line and "'" not in line and "`" not in line:
        return line
    return _INLINE_STRING_RE.sub('""', line)

# Rules with zero precision on external code (see docs/EXTERNAL_VALIDATION.md).
# They stay implemented and tested, but are OFF by default: a CI gate whose alerts
# are wrong most of the time gets disabled by its users within a week, and then the
# good rules go with it. Enable explicitly with --enable-rule.
#
# Measured precision on real merged PRs, wave 1 / wave 2:
#   assert_deletion             71% / 100%   on
#   weakened_test_skip          89% /  67%   on
#   silent_failure_empty_catch  17% /   0%   off
#   guard_removal                0% /   0%   off
#   phantom_stub                 0% /   0%   off
#   weakened_assertion           n/a /   0%   off
DEFAULT_OFF_RULES = frozenset({
    "silent_failure_empty_catch",
    "guard_removal",
    "phantom_stub",
    "weakened_assertion",
    "mock_substitution",
    "unconditional_accept",
})

def scan_diff_text(diff_text, allow_files=(), enable_rules=None):
    """Scanner for the classic LLM frauds across single and multi-line diff blocks.

    `allow_files` skips specific paths on request. Nothing is skipped silently:
    cmd_audit reports every exclusion it applies.
    """
    violations = []
    lines = diff_text.splitlines()

    allow_norm = {str(p).replace("\\", "/").lstrip("./") for p in allow_files}
    enabled = set(enable_rules or ())

    def _rule_on(name):
        if name in enabled:
            return True
        return name not in DEFAULT_OFF_RULES

    current_file = ""
    old_file = ""
    file_added_lines = {}
    file_deleted_lines = {}
    file_deleted_asserts = {}
    file_added_asserts = {}
    file_deleted_tests = {}
    file_added_tests = {}
    # Per-file open multi-line string delimiter, so single-line rules do not match
    # code that is actually data inside a triple-quoted fixture.
    file_string_state = {}

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

        # Skip synthetic test fixtures, benchmark scenarios and mocks, unless the
        # caller explicitly asked to audit them. Every skip is reported by cmd_audit.
        file_parts = current_file.lower().replace("\\", "/").split("/")
        if any(p in ("fixtures", "scenarios", "mocks") for p in file_parts[:-1]):
            continue
        if current_file.replace("\\", "/").lstrip("./") in allow_norm:
            continue

        if current_file not in file_added_lines:
            file_added_lines[current_file] = []
            file_deleted_lines[current_file] = []
            file_deleted_asserts[current_file] = 0
            file_added_asserts[current_file] = 0
            file_deleted_tests[current_file] = 0
            file_added_tests[current_file] = 0

        is_test = is_test_file(current_file)

        if line.startswith("+") and not line.startswith("+++"):
            code_line = line[1:].rstrip()
            file_added_lines[current_file].append(code_line)
            # Count added assertions (test files only)
            if is_code and is_test and (re.search(r"^\s*(await\s+)?(assert\b|expect\(|self\.assert\w+|mock\.\w*assert)", code_line)
                                        or RAISES_LINE_RE.search(code_line)):
                file_added_asserts[current_file] += 1
            # Count added test functions (test files only)
            if is_code and is_test and re.search(r"^\s*(def\s+test_\w+|it\s*\(|test\s*\()", code_line):
                file_added_tests[current_file] += 1

            # Single-line checks
            stripped_code = code_line.strip()
            # Skip embedded diff text fixtures inside test files (lines whose source text begins with '+')
            if stripped_code.startswith("+"):
                continue
            # Judge the code, not the string data it carries.
            judgeable = _strip_inline_strings(stripped_code)

            # Update multi-line string state for this file. A line that starts while
            # a block string is open is data, not code.
            open_delim = file_string_state.get(current_file)
            inside_block_string = open_delim is not None
            if open_delim is not None and stripped_code.count(open_delim) % 2 == 1:
                file_string_state[current_file] = None
            elif open_delim is None:
                for delim in ('"""', "'''", "`"):
                    if stripped_code.count(delim) % 2 == 1:
                        file_string_state[current_file] = delim
                        break
            if inside_block_string:
                continue

            is_comment = stripped_code.startswith("#") or stripped_code.startswith("//") or stripped_code.startswith('"""') or stripped_code.startswith("'''") or stripped_code.startswith("*")
            for key, (pattern, desc) in FRAUD_PATTERNS.items():
                if not is_code and key != "obsolete_ai_model_reference":
                    continue
                # Scoping: Test skip and test weakening rules ONLY apply to test files
                if key == "weakened_test_skip" and not is_test:
                    continue
                if is_comment and key in ("silent_failure_empty_catch", "phantom_stub", "tautological_assertion"):
                    continue
                # In obsolete_ai_model_reference: allow comments documenting migration/legacy context
                if key == "obsolete_ai_model_reference" and is_comment:
                    continue
                if is_comment and key == "weakened_test_skip" and not re.search(r"(#|//)\s*(assert\b|expect\()", stripped_code):
                    continue
                # Match against the code with string contents blanked out — except for
                # model identifiers, which are *supposed* to live inside string literals.
                target = stripped_code if key == "obsolete_ai_model_reference" else judgeable
                if re.search(pattern, target):
                    violations.append({
                        "file": current_file,
                        "line": stripped_code,
                        "fraud_type": key,
                        "description": desc
                    })

        elif line.startswith("-") and not line.startswith("---"):
            code_line = line[1:].rstrip()
            file_deleted_lines[current_file].append(code_line)
            # Count deleted assertions (test files only)
            if is_code and is_test and (re.search(r"^\s*(await\s+)?(assert\b|expect\(|self\.assert\w+|mock\.\w*assert)", code_line)
                                        or RAISES_LINE_RE.search(code_line)):
                file_deleted_asserts[current_file] += 1
            # Count deleted test functions (test files only)
            if is_code and is_test and re.search(r"^\s*(def\s+test_\w+|it\s*\(|test\s*\()", code_line):
                file_deleted_tests[current_file] += 1

    # Check for net assert deletions per file (test files only)
    for fname, del_count in file_deleted_asserts.items():
        if not is_test_file(fname):
            continue
        add_count = file_added_asserts.get(fname, 0)
        if del_count > add_count:
            violations.append({
                "file": fname,
                "line": f"Deleted {del_count} assertions vs {add_count} added",
                "fraud_type": "assert_deletion",
                "description": f"Net assertion deletion detected ({del_count - add_count} assertions removed without replacement)"
            })

    # Check for net test function deletions per file (test files only)
    for fname, del_t in file_deleted_tests.items():
        if not is_test_file(fname):
            continue
        add_t = file_added_tests.get(fname, 0)
        if del_t > add_t:
            violations.append({
                "file": fname,
                "line": f"Deleted {del_t} test functions vs {add_t} added",
                "fraud_type": "weakened_test_skip",
                "description": f"Net test function deletion detected ({del_t - add_t} test functions deleted without replacement)"
            })

    # Paired-line analysis: a test assertion that was replaced by a weaker one is
    # invisible to per-line regexes, because each line is individually plausible.
    # Compare what was removed against what took its place.
    for fname, added in file_added_lines.items():
        deleted = file_deleted_lines.get(fname, [])
        if not deleted or not added:
            continue
        if not is_test_file(fname):
            continue
        if not any(fname.lower().endswith(ext) for ext in CODE_EXTENSIONS):
            continue
        old_strengths = [s for s in (_assert_strength(l) for l in deleted) if s]
        new_strengths = [s for s in (_assert_strength(l) for l in added) if s]
        strong_removed = old_strengths.count("strong")
        strong_present = new_strengths.count("strong")
        weak_added = new_strengths.count("weak")
        if strong_removed > strong_present and weak_added > 0:
            violations.append({
                "file": fname,
                "line": "assertion weakened on replacement",
                "fraud_type": "weakened_assertion",
                "description": (
                    f"A concrete assertion was replaced by a weaker one "
                    f"({strong_removed} strong removed, {strong_present} strong present, "
                    f"{weak_added} weak added)"
                )
            })

    # Guard removal: a validation branch was deleted and nothing replaced it.
    for fname, deleted in file_deleted_lines.items():
        if not deleted:
            continue
        if not any(fname.lower().endswith(ext) for ext in CODE_EXTENSIONS):
            continue
        added = file_added_lines.get(fname, [])
        guards_removed = _count_guards(deleted)
        guards_added = _count_guards(added)
        if guards_removed > guards_added:
            first = next((l.strip() for l in deleted if GUARD_LINE_RE.match(l)), "")
            violations.append({
                "file": fname,
                "line": first,
                "fraud_type": "guard_removal",
                "description": (
                    f"Validation branch removed without replacement "
                    f"({guards_removed - guards_added} guard clause(s) deleted)"
                )
            })

    # Guard boundary loosened: same number of guards, weaker comparison.
    for fname, deleted in file_deleted_lines.items():
        added = file_added_lines.get(fname, [])
        if not added or not deleted:
            continue
        if not any(fname.lower().endswith(ext) for ext in CODE_EXTENSIONS):
            continue
        old = [(m.group(1), m.group(2)) for l in deleted for m in [GUARD_BOUNDARY_RE.search(l)] if m]
        new = [(m.group(1), m.group(2)) for l in added for m in [GUARD_BOUNDARY_RE.search(l)] if m]
        for old_op, old_val in old:
            for new_op, new_val in new:
                if old_val != new_val:
                    continue
                if STRICTER.get(new_op) == old_op:
                    violations.append({
                        "file": fname,
                        "line": f"{old_op} {old_val} -> {new_op} {new_val}",
                        "fraud_type": "guard_removal",
                        "description": (
                            f"Guard boundary loosened ({old_op} {old_val} became {new_op} {new_val}); "
                            f"the rejected input range shrank"
                        )
                    })
                    break

    # Multiline block scanner: comment-tolerant, whitespace-tolerant
    for fname, added in file_added_lines.items():
        if not any(fname.lower().endswith(ext) for ext in CODE_EXTENSIONS):
            continue
        n = len(added)
        in_string = _strip_string_context(added)
        for i in range(n):
            if i in in_string:
                continue
            line_i = added[i].strip()
            # Blank string contents so fixture code inside one line is not judged.
            line_i_judged = _strip_inline_strings(line_i)

            # Python except block: judge the whole handler body, not just the next token
            if re.match(r"^except\b[^:]*:", line_i_judged):
                body = []
                for j in range(i + 1, min(i + 10, n)):
                    stmt = added[j]
                    if not stmt.strip():
                        continue
                    indent = len(stmt) - len(stmt.lstrip())
                    if indent <= len(line_i) - len(line_i.lstrip()):
                        break
                    body.append(stmt.strip())
                _judge_handler(body, fname, line_i, "python", violations,
                               context_lines=added[max(0, i - 4):i + 1])

            # JS/TS catch block: same treatment
            if re.search(r"(?<!\.)\bcatch(\s*\([^\)]*\))?\s*\{", line_i_judged) or re.match(r"^\}?\s*catch(\s*\([^\)]*\))?\s*$", line_i_judged):
                body = []
                # Count braces only from the `catch` keyword onward: a leading `}`
                # closes the try block, not the handler body.
                catch_at = line_i.find("catch")
                rest = line_i[catch_at:] if catch_at >= 0 else line_i
                depth = rest.count("{") - rest.count("}")
                if depth <= 0:
                    _judge_handler(body, fname, line_i, "javascript", violations)
                else:
                    for j in range(i + 1, min(i + 10, n)):
                        stmt = added[j]
                        for ch in stmt:
                            if ch == "{":
                                depth += 1
                            elif ch == "}":
                                depth -= 1
                        if depth <= 0:
                            break
                        body.append(stmt.strip())
                    _judge_handler(body, fname, line_i, "javascript", violations)

            # Mock substitution: patching a method on an existing object replaces the
            # unit under test, so the assertion only verifies the mock.
            if is_test and (MOCK_PATCH_RE.match(line_i_judged) or MOCK_SPY_RE.search(line_i_judged)):
                violations.append({
                    "file": fname,
                    "line": line_i,
                    "fraud_type": "mock_substitution",
                    "description": "Mock assigned over an object method inside a test (unit under test replaced)"
                })

            # Unconditional accept: a validation-shaped function whose only body line
            # returns a success value, with no branch before it.
            for fn_regex, ret_regex in (
                (r"^def\s+(\w*(?:valid|check|verif|auth|allow|perm|guard)\w*)\s*\(.*\)\s*:", r"^return\s+(True|1)\s*$"),
                (r"^(?:function\s+(\w*(?:valid|check|verif|auth|allow|perm|guard|can)\w*)|(?:const|let)\s+(\w*(?:valid|check|verif|auth|allow|perm|guard|can)\w*)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>)\s*\{?", r"^return\s+(true|1)\s*;?$"),
            ):
                m_fn = re.match(fn_regex, line_i_judged)
                if not m_fn:
                    continue
                body = []
                for j in range(i + 1, min(i + 6, n)):
                    stmt = added[j].strip()
                    if not stmt or stmt.startswith(("#", "//")):
                        continue
                    if stmt in ("}", "};"):
                        break
                    body.append(stmt)
                if len(body) == 1 and re.match(ret_regex, body[0]):
                    violations.append({
                        "file": fname,
                        "line": f"{line_i} ... {body[0]}",
                        "fraud_type": "unconditional_accept",
                        "description": "Validation function unconditionally returns success"
                    })

            # Function stub check (Python and JS/TS)
            is_py_func = re.match(r"^def\s+\w+\s*\(.*\)\s*:", line_i_judged)
            # Only a STATEMENT-position function can have a body we can inspect.
            # `defineProps(function chalk() {}, styles)` passes a function
            # EXPRESSION as an argument; its `{}` is the whole body, not a stub.
            # Anchoring at column 0 rejects the argument form.
            is_js_func = re.match(
                r"^(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s+\w+\s*\([^)]*\)\s*\{",
                line_i_judged
            ) or re.match(
                r"^(?:const|let|var)\s+\w+\s*=\s*(?:async\s*)?(?:\([^)]*\)|\w+)\s*=>\s*\{",
                line_i_judged
            )

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
                # If the block opens and closes on the same line, the "body" is on this
                # line — never the empty body of the following lines. Inline `{}` is a
                # deliberate no-op or a prototype target, not an unfinished stub.
                opens = line_i_judged.count("{")
                closes = line_i_judged.count("}")
                if opens > 0 and closes >= opens:
                    break_after = True
                else:
                    break_after = False
                if not break_after:
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

    return [v for v in violations if _rule_on(v["fraud_type"])]


def cmd_audit(args):
    root = find_repo_root()
    state = load_state(root)
    base_branch = getattr(args, "base", None)
    if not base_branch:
        check_main = subprocess.run(["git", "rev-parse", "--verify", "main"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=root)
        base_branch = "main" if check_main.returncode == 0 else "master"
    
    # Identify targets: active worktree (if registered and exists) and/or repo root
    targets_to_audit = []
    active_wt = getattr(args, "worktree", None) or state.get("active_worktree")
    if active_wt and not getattr(args, "root_only", False):
        wt_path = Path(active_wt).resolve()
        # Only audit the worktree separately when it is genuinely a different
        # tree. Passing --worktree pointing at the repo itself audited the same
        # files twice, and every finding was reported in duplicate.
        if wt_path.exists() and wt_path != Path(root).resolve():
            targets_to_audit.append(("active_worktree", wt_path))

    targets_to_audit.append(("repo_root", root))

    print(f"🔍 Running KAIROS Adversarial Zero-Trust Audit against '{base_branch}'...")

    all_diff_texts = []
    for label, target_path in targets_to_audit:
        diff_text = ""
        try:
            diff_res = subprocess.run(["git", "diff", f"{base_branch}...HEAD"],
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=target_path)
            if diff_res.returncode == 0 and diff_res.stdout.strip():
                diff_text += diff_res.stdout
        except (subprocess.SubprocessError, OSError):
            diff_res = None

        # Include staged working tree diff (--cached)
        try:
            staged_diff = subprocess.run(["git", "diff", "--cached"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=target_path)
            if staged_diff.returncode == 0 and staged_diff.stdout.strip():
                diff_text += "\n" + staged_diff.stdout
        except (subprocess.SubprocessError, OSError):
            staged_diff = None
        
        # Include unstaged working tree diff
        try:
            unstaged_diff = subprocess.run(["git", "diff"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=target_path)
            if unstaged_diff.returncode == 0 and unstaged_diff.stdout.strip():
                diff_text += "\n" + unstaged_diff.stdout
        except (subprocess.SubprocessError, OSError):
            unstaged_diff = None

        # Include untracked files as synthetic additions
        try:
            untracked_res = subprocess.run(
                ["git", "ls-files", "--others", "--exclude-standard"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=target_path
            )
            if untracked_res.returncode == 0 and untracked_res.stdout.strip():
                for rel_path_str in untracked_res.stdout.splitlines():
                    rel_path_str = rel_path_str.strip()
                    if not rel_path_str or rel_path_str.startswith(".git/"):
                        continue
                    ext = "." + rel_path_str.rsplit(".", 1)[-1].lower() if "." in rel_path_str else ""
                    if ext in ALL_AUDIT_EXTENSIONS:
                        untracked_file = target_path / rel_path_str
                        if untracked_file.is_file():
                            try:
                                content = untracked_file.read_text(encoding="utf-8", errors="replace")
                                file_lines = content.splitlines()
                                synth = f"--- /dev/null\n+++ b/{rel_path_str}\n@@ -0,0 +1,{len(file_lines)} @@\n"
                                synth += "\n".join(f"+{l}" for l in file_lines)
                                diff_text += "\n" + synth
                            except OSError:
                                content = None
        except (subprocess.SubprocessError, OSError):
            untracked_res = None

        if diff_text.strip():
            all_diff_texts.append(diff_text)

    combined_diff = "\n".join(all_diff_texts)
    if not combined_diff.strip():
        print("ℹ️ Diff is empty. No changes detected to audit.")
        return 0

    allow_files = tuple(getattr(args, "allow_file", None) or ())
    if allow_files:
        print(f"⚠️  Explicitly excluded from this audit: {', '.join(allow_files)}")

    enabled_rules = tuple(getattr(args, "enable_rule", None) or ())
    off_rules = sorted(DEFAULT_OFF_RULES - set(enabled_rules))
    if off_rules:
        print(f"ℹ️  Rules disabled by default (0% external precision): {', '.join(off_rules)}")
        print(f"    Enable with --enable-rule <name>. See docs/EXTERNAL_VALIDATION.md")

    violations = scan_diff_text(combined_diff, allow_files=allow_files,
                                enable_rules=enabled_rules)

    # A clean diff is not proof that the tests are strong. Require a current
    # K-Mutant report with zero survivors before granting VERIFIED.
    k_dir = get_kairos_dir(root)
    kmutant = None
    kmutant_path = k_dir / "kmutant_latest.json"
    if kmutant_path.exists():
        try:
            kmutant = json.loads(kmutant_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            kmutant = None
    mutation_ok = bool(kmutant) and kmutant.get("survived") == 0

    print("=================================================================")
    print("🛡️  KAIROS ADVERSARIAL AUDIT REPORT")
    print("=================================================================")

    if not violations and not mutation_ok:
        reason = "no kmutant_latest.json found" if not kmutant else (
            f"{kmutant.get('survived')} mutant(s) survived in {kmutant.get('target', '?')}"
        )
        audit_report = {
            "verdict": "REPAIR",
            "violations": [],
            "violation_count": 0,
            "mutation_gate": "FAILED",
            "mutation_reason": reason,
            "timestamp": datetime.now().isoformat(),
            "base_branch": base_branch
        }
        try:
            k_dir.mkdir(parents=True, exist_ok=True)
            (k_dir / "audit_latest.json").write_text(json.dumps(audit_report, indent=2), encoding="utf-8")
        except OSError as e:
            print(f"⚠️  Could not persist audit report: {e}", file=sys.stderr)
        state = load_state(root)
        state["current_stage"] = "REPAIR_REQUIRED"
        save_state(state, root)
        print("VERDICT: [ 🟡 REPAIR ]")
        print("• No diff fraud detected, but test strength was not proven.")
        print(f"• Mutation gate: FAILED ({reason})")
        print("• Prove the tests catch something: break the code by hand and watch them fail.")
        print("=================================================================")
        return 1

    audit_report = {
        "verdict": "VERIFIED" if not violations else "REFUTED",
        "violations": violations,
        "violation_count": len(violations),
        "timestamp": datetime.now().isoformat(),
        "base_branch": base_branch
    }
    try:
        (k_dir / "audit_latest.json").write_text(json.dumps(audit_report, indent=2), encoding="utf-8")
    except Exception as e:
        print(f"Warning: could not write latest audit report: {e}", file=sys.stderr)

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
        # Persist the refutation too. A verdict that leaves no artifact is the
        # one you cannot review later, and finding a fraud is exactly when the
        # evidence matters most.
        try:
            k_dir = get_kairos_dir(root)
            k_dir.mkdir(parents=True, exist_ok=True)
            (k_dir / "audit_latest.json").write_text(
                json.dumps(audit_report, indent=2), encoding="utf-8")
        except OSError as e:
            print(f"⚠️  Could not persist audit report: {e}", file=sys.stderr)
        print("VERDICT: [ ❌ REFUTED - FRAUD OR WEAKENED CHECKS DETECTED ]")
        print(f"Found {len(violations)} suspicious pattern(s):\n")
        for idx, v in enumerate(violations, 1):
            print(f" [{idx}] {v['description'].upper()}")
            print(f"     File: {v['file']}")
            print(f"     Line: {v['line']}")
        print("=================================================================")
        print("Action required: Resolve all violations before progressing to Ship.")
        return 1

def cmd_brainstorm(args):
    """Scaffold or check the brainstorm brief that precedes a spec."""
    import kairos_brainstorm

    if getattr(args, "new", None):
        target = Path(args.out or kairos_brainstorm.BRIEF_NAME)
        if target.exists():
            print(f"⚠️  Refusing to overwrite existing brief: {target}")
            return 1
        target.write_text(kairos_brainstorm.TEMPLATE.format(name=args.new), encoding="utf-8")
        print(f"✅ Wrote {target}")
        print("   Fill it before `kairos spec`. A blank brief is worse than none.")
        return 0

    if getattr(args, "check", None):
        p = Path(args.check).expanduser()
        if not p.is_file():
            print(f"❌ Not found: {p}", file=sys.stderr)
            return 1
        result = kairos_brainstorm.check_brief(p.read_text(encoding="utf-8", errors="replace"))
        icon = "✅" if result["ok"] else "🟡"
        print("=" * 68)
        print(f"{icon} BRAINSTORM — {'OK' if result['ok'] else 'INCOMPLETE'}")
        print("=" * 68)
        print(f"  alternatives:     {result['alternatives']} "
              f"(need {kairos_brainstorm.MIN_ALTERNATIVES})")
        print(f"  without reason:   {result['unresolved']}")
        print(f"  present:          {', '.join(result['sections_present']) or 'none'}")
        if result["sections_missing"]:
            print(f"  missing:          {', '.join(result['sections_missing'])}")
        for p_ in result["problems"]:
            print(f"  - {p_}")
        print("=" * 68)
        return 0 if result["ok"] else 1

    print("Use `kairos brainstorm --new <name>` or `--check <path>`.")
    return 1


def cmd_gate(args):
    """Verify the delivered diff against the spec that authorised it."""
    import kairos_gate

    spec_path = Path(args.spec).expanduser()
    if not spec_path.exists():
        print(f"❌ Spec not found: {spec_path}", file=sys.stderr)
        return 1

    target = Path(args.worktree).expanduser() if args.worktree else find_repo_root()
    diff_res = subprocess.run(["git", "diff", f"{args.base}...HEAD"],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              text=True, cwd=target)
    if diff_res.returncode != 0:
        print(f"❌ git diff failed against '{args.base}': {diff_res.stderr.strip()}", file=sys.stderr)
        return 1
    diff_text = diff_res.stdout

    # Include uncommitted work: the gate judges what is about to ship, not only
    # what is already committed.
    for extra in (["diff", "--cached"], ["diff"]):
        res = subprocess.run(["git"] + extra, stdout=subprocess.PIPE,
                             stderr=subprocess.DEVNULL, text=True, cwd=target)
        if res.returncode == 0 and res.stdout.strip():
            diff_text += "\n" + res.stdout

    if not diff_text.strip():
        print("ℹ️ No diff against that base. Nothing to verify.")
        return 0

    verification = None
    verify_cmd = getattr(args, "verify", None)
    as_json = getattr(args, "json", False)
    if verify_cmd:
        # Progress goes to stderr when --json is requested, so stdout stays a
        # single parseable document. A CI job doing `gate --json > out.json`
        # otherwise gets a file that json.loads rejects.
        progress = sys.stderr if as_json else sys.stdout
        print(f"▶ Re-running the claimed verification: {verify_cmd}", file=progress)
        verification = kairos_gate.run_verification(str(verify_cmd), cwd=str(target))
        status = verification["exit_code"]
        print(f"  exit={status} in {verification['duration_s']}s", file=progress)
        if verification["tail"]:
            for ln in verification["tail"][-5:]:
                print(f"    {ln[:110]}", file=progress)
        print(file=progress)

    result = kairos_gate.gate(
        kairos_gate.parse_spec(spec_path),
        diff_text,
        allow_fraud_rules=tuple(args.enable_rule or ()),
        verification=verification,
    )

    state = load_state(target)
    state["current_stage"] = {"READY": "VERIFIED", "REPAIR": "REPAIR_REQUIRED",
                              "BLOCKED": "REPAIR_REQUIRED"}[result["verdict"]]
    save_state(state, target)

    try:
        k_dir = get_kairos_dir(target)
        k_dir.mkdir(parents=True, exist_ok=True)
        (k_dir / "gate_latest.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    except OSError:
        pass

    if args.json:
        print(json.dumps(result, indent=2))
        return 0 if result["verdict"] == "READY" else 1

    icon = {"READY": "✅", "REPAIR": "🟡", "BLOCKED": "⛔"}[result["verdict"]]
    print("=" * 68)
    print(f"{icon} KAIROS GATE — {result['verdict']}")
    print("=" * 68)
    print(f"  spec:            {Path(result['spec']).name}")
    print(f"  completeness:    {result['completeness']}/8 "
          f"(threshold {kairos_gate.COMPLETENESS_THRESHOLD})")
    print(f"  acceptance:      {result['criteria']} criteria")
    print(f"  diff:            {len(result['diff']['files'])} file(s), "
          f"+{result['diff']['added']}/-{result['diff']['removed']} lines")
    if result.get("verification"):
        v = result["verification"]
        print(f"  verification:    `{v['command']}` -> exit {v['exit_code']} "
              f"({v['duration_s']}s)")
    else:
        print("  verification:    NOT RUN — no --verify given, so 'tests pass' is a claim")
    if result["findings"]:
        print("  findings:")
        for f in result["findings"]:
            print(f"    [{f['severity']:<7}] {f['rule']}")
            print(f"              {f['detail']}")
            if f.get("evidence"):
                print(f"              basis: {f['evidence']}")
    else:
        print("  findings:        none")
    print("=" * 68)
    return 0 if result["verdict"] == "READY" else 1


def cmd_fit(args):
    """Spec Fit Test: the benchmark found no gain on small tickets."""
    import kairos_gate

    answers = [
        args.touches >= 3,
        args.criteria >= 4,
        args.crosses_boundary,
        args.changes_schema_or_api,
        args.multiple_owners,
        args.regulated,
    ]
    result = kairos_gate.fit_test(answers)
    print("=" * 68)
    print(f"SPEC FIT TEST — {result['verdict']} "
          f"({result['score']}/{result['of']}, threshold {result['threshold']})")
    print("=" * 68)
    for statement, answered in zip(result["statements"], answers):
        print(f"  [{'x' if answered else ' '}] {statement}")
    print("-" * 68)
    if result["verdict"] == "SPEC":
        print("  Write a spec. The benchmark paid back its overhead on this size.")
    else:
        print("  Skip the spec: give the ticket text and acceptance criteria, then review.")
        print("  On bug-fix, refactor and test-writing tickets the measured gain was 0pp")
        print("  while the spec phase cost ~18 minutes and ~35% of the tokens.")
    print("=" * 68)
    return 0

# ---------------------------------------------------------------------------
# MAIN CLI DISPATCHER
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# MAIN CLI DISPATCHER
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        prog="kairos",
        description="Checks a coding agent cannot do for itself. "
                    "See docs/EVIDENCE.md for what each one is based on.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init", help="Create .kairos/ in this repository")

    p_fit = subparsers.add_parser(
        "fit", help="Spec Fit Test: decide whether a ticket justifies a spec")
    p_fit.add_argument("--touches", type=int, default=0,
                       help="Number of files the change likely touches")
    p_fit.add_argument("--criteria", type=int, default=0,
                       help="Number of acceptance criteria")
    p_fit.add_argument("--crosses-boundary", action="store_true")
    p_fit.add_argument("--changes-schema-or-api", action="store_true")
    p_fit.add_argument("--multiple-owners", action="store_true")
    p_fit.add_argument("--regulated", action="store_true")

    p_bs = subparsers.add_parser(
        "brainstorm", help="Scaffold or check the brief that precedes a spec")
    p_bs.add_argument("--new", metavar="NAME", help="Write a brief template")
    p_bs.add_argument("--check", metavar="PATH", help="Check an existing brief")
    p_bs.add_argument("--out", default=None, help="Output path for --new")

    p_spec = subparsers.add_parser("spec", help="Scaffold the eight-section spec")
    p_spec.add_argument("name", help="Short name of the change")

    p_gate = subparsers.add_parser(
        "gate", help="Verify the delivered diff against its spec (exit 0 = READY)")
    p_gate.add_argument("--spec", required=True, help="Path to the spec or design document")
    p_gate.add_argument("--base", default="main", help="Base ref to diff against")
    p_gate.add_argument("--worktree", default=None, help="Repository path to diff in")
    p_gate.add_argument("--json", action="store_true", help="Machine-readable output")
    p_gate.add_argument("--enable-rule", action="append", default=[], metavar="NAME",
                        help="Enable a scanner rule that is off by default")
    p_gate.add_argument("--verify", default=None, metavar="CMD",
                        help="Command to re-run as evidence, e.g. 'pytest -q'. "
                             "Without it, any claim that tests pass stays unverified.")

    p_audit = subparsers.add_parser(
        "audit", help="Scan the current diff for fraud patterns")
    p_audit.add_argument("--base", default="main", help="Base branch to diff against")
    p_audit.add_argument("--worktree", default=None, help="Specific worktree path to audit")
    p_audit.add_argument("--root-only", action="store_true", help="Ignore the active worktree")
    p_audit.add_argument("--allow-file", action="append", default=[], metavar="PATH",
                         help="Exclude a specific path (repeated; reported in the output)")
    p_audit.add_argument("--enable-rule", action="append", default=[], metavar="NAME",
                         help="Enable a scanner rule that is off by default")

    args = parser.parse_args()

    dispatch = {
        "init": cmd_init,
        "fit": cmd_fit,
        "brainstorm": cmd_brainstorm,
        "spec": cmd_spec,
        "gate": cmd_gate,
        "audit": cmd_audit,
    }

    try:
        exit_code = dispatch[args.command](args)
        sys.exit(exit_code or 0)
    except FileNotFoundError as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
