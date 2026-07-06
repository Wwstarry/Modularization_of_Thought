"""
CodeCoT baseline for code generation.

Reference: Yao et al., "CodeCoT: Tackling Code Syntax Errors in CoT
Reasoning for Code Generation", arXiv 2023 / EMNLP 2024.

Three-phase self-examination pipeline (independent implementation):
  1. Generate initial code via CoT reasoning.
  2. Generate test cases that the code should pass.
  3. Execute code against tests; if failures exist, repair iteratively.

Uses mot.executor for sandboxed code execution.
"""
from __future__ import annotations

import logging
from typing import List

from mot.executor import execute_code
from mot.llm import LLMClient
from mot.mot_engine import _extract_code
from mot.prompts import (
    CODECOT_INITIAL_CODE_SYSTEM,
    CODECOT_INITIAL_CODE_TEMPLATE,
    CODECOT_TEST_GEN_SYSTEM,
    CODECOT_TEST_GEN_TEMPLATE,
    CODECOT_REPAIR_SYSTEM,
    CODECOT_REPAIR_TEMPLATE,
)

logger = logging.getLogger(__name__)

_MAX_REPAIR_ROUNDS = 3
_MAX_TEST_CASES = 5
_EXEC_TIMEOUT = 30


class CodeCoT:
    """
    CodeCoT prompting baseline: CoT + test generation + iterative self-repair.

    Parameters
    ----------
    llm : LLMClient
    max_repair_rounds : int
        Maximum number of repair iterations (default: 3, as in the paper).
    max_test_cases : int
        Maximum number of test cases to generate (default: 5).
    exec_timeout : int
        Code execution timeout in seconds (default: 30).
    """

    def __init__(
        self,
        llm: LLMClient,
        max_repair_rounds: int = _MAX_REPAIR_ROUNDS,
        max_test_cases: int = _MAX_TEST_CASES,
        exec_timeout: int = _EXEC_TIMEOUT,
    ) -> None:
        self.llm = llm
        self.max_repair_rounds = max_repair_rounds
        self.max_test_cases = max_test_cases
        self.exec_timeout = exec_timeout

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(self, task_description: str, entry_point: str = "") -> str:
        """
        Run the CodeCoT pipeline and return the final Python code.

        1. Generate initial code (CoT-style).
        2. Generate test cases.
        3. Execute and repair iteratively (up to max_repair_rounds).
        """
        task = task_description.strip()

        # Phase 1: initial code generation
        code = self._generate_initial_code(task, entry_point)

        # Phase 2: test case generation
        tests = self._generate_test_cases(task, entry_point)

        # Phase 3: execute and repair
        for rnd in range(self.max_repair_rounds):
            status, failed, errors = execute_code(code, tests, self.exec_timeout)
            if status == "pass":
                logger.debug("CodeCoT: all tests passed after %d repair round(s)", rnd)
                break
            logger.debug(
                "CodeCoT: repair round %d/%d — %d tests failed",
                rnd + 1, self.max_repair_rounds, len(failed),
            )
            code = self._repair(task, code, failed, errors, entry_point)

        return code

    # ------------------------------------------------------------------
    # Internal phases
    # ------------------------------------------------------------------

    def _generate_initial_code(self, task: str, entry_point: str) -> str:
        user_content = CODECOT_INITIAL_CODE_TEMPLATE.format(task=task)
        raw = self.llm.chat(
            [{"role": "user", "content": user_content}],
            system=CODECOT_INITIAL_CODE_SYSTEM,
        )
        return _extract_code(raw, entry_point)

    def _generate_test_cases(self, task: str, entry_point: str) -> List[str]:
        user_content = CODECOT_TEST_GEN_TEMPLATE.format(task=task)
        raw = self.llm.chat(
            [{"role": "user", "content": user_content}],
            system=CODECOT_TEST_GEN_SYSTEM,
        )
        tests = _parse_test_cases(raw)
        return tests[: self.max_test_cases]

    def _repair(
        self,
        task: str,
        code: str,
        failed_tests: List[str],
        error_details: List[str],
        entry_point: str,
    ) -> str:
        user_content = CODECOT_REPAIR_TEMPLATE.format(
            code=code,
            failed_tests="\n".join(failed_tests),
            error_details="\n".join(error_details),
        )
        raw = self.llm.chat(
            [{"role": "user", "content": user_content}],
            system=CODECOT_REPAIR_SYSTEM,
        )
        return _extract_code(raw, entry_point)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_test_cases(raw: str) -> List[str]:
    """
    Extract assert statements from the LLM test-generation response.

    Strips code fences and blank lines; returns only lines that start
    with "assert " (case-insensitive stripped).
    """
    # Remove fenced blocks if present
    lines = raw.strip().splitlines()
    cleaned: List[str] = []
    in_fence = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence or not stripped:
            if not in_fence and not stripped:
                continue
            if in_fence:
                cleaned.append(stripped)
        else:
            cleaned.append(stripped)

    # Keep only assert statements
    tests = [ln for ln in cleaned if ln.lower().startswith("assert ")]
    return tests
