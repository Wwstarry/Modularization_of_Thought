"""
Self-contained sandboxed Python code executor.

Runs generated Python code in an isolated subprocess with a configurable
timeout. No external dependencies — uses only the Python standard library.

Public API
----------
syntax_check(code)                   → bool
execute_code(code, test_cases, ...)  → (status, failed_assertions, error_details)
count_passed(code, test_cases, ...)  → int
"""
from __future__ import annotations

import ast
import os
import sys
import subprocess
import tempfile
import textwrap
from typing import List, Tuple


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def syntax_check(code: str) -> bool:
    """Return True if *code* parses without a SyntaxError."""
    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False


def execute_code(
    code: str,
    test_cases: List[str],
    timeout: int = 30,
) -> Tuple[str, List[str], List[str]]:
    """
    Execute *code* against each test case string in *test_cases*.

    Each element of *test_cases* is expected to be a Python assert statement
    (e.g. ``"assert f(1) == 2"``).

    Returns
    -------
    status : "pass" | "fail"
    failed_assertions : list of raw assert strings that failed
    error_details     : list of "FAILED: <assert>\\n  <error>" strings
    """
    if not syntax_check(code):
        return "fail", list(test_cases), ["SyntaxError: code could not be parsed"]

    if not test_cases:
        rc, out = _run_snippet(code, timeout)
        return ("pass" if rc == 0 else "fail"), [], ([] if rc == 0 else [out])

    failed_assertions: List[str] = []
    error_details: List[str] = []

    for tc in test_cases:
        full = _build_test_script(code, tc)
        rc, out = _run_snippet(full, timeout)
        if rc != 0:
            failed_assertions.append(tc.strip())
            error_details.append(f"FAILED: {tc.strip()}\n  {out.strip()}")

    if not failed_assertions:
        return "pass", [], []
    return "fail", failed_assertions, error_details


def count_passed(
    code: str,
    test_cases: List[str],
    timeout: int = 30,
) -> int:
    """Return the number of test cases *code* passes (no short-circuit)."""
    if not syntax_check(code) or not test_cases:
        return 0
    passed = 0
    for tc in test_cases:
        full = _build_test_script(code, tc)
        rc, _ = _run_snippet(full, timeout)
        if rc == 0:
            passed += 1
    return passed


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _build_test_script(code: str, test_case: str) -> str:
    """Combine user code with a single assert statement for execution."""
    return textwrap.dedent(f"""\
{code}

# ---- auto-generated test ----
try:
    {test_case.strip()}
except AssertionError as _e:
    import sys
    print(f"AssertionError: {{_e}}", file=sys.stderr)
    sys.exit(1)
except Exception as _e:
    import sys
    print(f"{{type(_e).__name__}}: {{_e}}", file=sys.stderr)
    sys.exit(1)
""")


def _run_snippet(code: str, timeout: int) -> Tuple[int, str]:
    """
    Write *code* to a temp file and execute it with the current interpreter.

    Returns (returncode, combined stdout+stderr).
    """
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as f:
        f.write(code)
        tmp_path = f.name

    try:
        result = subprocess.run(
            [sys.executable, tmp_path],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = (result.stdout + result.stderr).strip()
        return result.returncode, output
    except subprocess.TimeoutExpired:
        return 1, f"TimeoutError: execution exceeded {timeout}s"
    except Exception as exc:
        return 1, f"{type(exc).__name__}: {exc}"
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
