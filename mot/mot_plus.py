"""
MoT+ (Modularization-of-Thought Plus) Engine.

An enhanced variant of MoT (arXiv:2503.12483) that adds a third phase:
**execution-guided repair**. Starting from MoT's stronger modular baseline,
MoT+ runs the generated code against docstring-derived test cases and
iteratively repairs any failures.

Three-phase pipeline
--------------------
Phase 1: Enhanced MLR Graph Generation
  - Uses MLR_GRAPH_SYSTEM_PLUS (richer system prompt with a concrete
    few-shot MLR example, no over-engineering of input validation).

Phase 2: Modular Code Generation
  - Guided by the richer MLR graph; demands strict adherence to docstring spec.

Phase 3: Execution-guided Self-repair  ← NEW
  1. Extract doctest examples from the problem prompt (most reliable tests).
  2. If few/no doctests, supplement with LLM-generated tests.
  3. Run Phase-2 code against those tests.
  4. If failures exist, prompt the LLM to repair, keeping MLR graph in context.
  5. Repeat up to max_repair_rounds.
"""
from __future__ import annotations

import re
import logging
from typing import List, Tuple

from mot.executor import execute_code
from mot.llm import LLMClient
from mot.mot_engine import _extract_code
from mot.prompts import (
    # Phase 1: use original MoT prompts (proven to be best for MLR graph)
    MLR_GRAPH_PROMPT,
    # Phase 2: use original MoT prompts for code generation
    CODE_GEN_SYSTEM,
    CODE_GEN_PROMPT_TEMPLATE,
    # Phase 3: repair prompts (new, added by MoT+)
    MOTPLUS_REPAIR_SYSTEM,
    MOTPLUS_REPAIR_TEMPLATE,
    MOTPLUS_TEST_GEN_SYSTEM,
    MOTPLUS_TEST_GEN_TEMPLATE,
)

logger = logging.getLogger(__name__)

_DEFAULT_MAX_REPAIR_ROUNDS = 3
_DEFAULT_N_TESTS = 6
_DEFAULT_EXEC_TIMEOUT = 30


class MoTPlusEngine:
    """
    MoT+ three-phase engine: enhanced MLR graph → modular code → repair loop.

    Parameters
    ----------
    llm : LLMClient
    max_repair_rounds : int
        Maximum self-repair iterations (default: 3).
    n_tests : int
        Max number of LLM-generated supplementary tests (default: 6).
    exec_timeout : int
        Code execution timeout per test, in seconds (default: 30).
    """

    def __init__(
        self,
        llm: LLMClient,
        max_repair_rounds: int = _DEFAULT_MAX_REPAIR_ROUNDS,
        n_tests: int = _DEFAULT_N_TESTS,
        exec_timeout: int = _DEFAULT_EXEC_TIMEOUT,
    ) -> None:
        self.llm = llm
        self.max_repair_rounds = max_repair_rounds
        self.n_tests = n_tests
        self.exec_timeout = exec_timeout

    # ------------------------------------------------------------------
    # Public API  (same interface as MoTEngine)
    # ------------------------------------------------------------------

    def generate(
        self,
        task_description: str,
        entry_point: str = "",
    ) -> Tuple[str, str]:
        """
        Run the full MoT+ pipeline.

        Returns
        -------
        code : str — final (repaired) Python code
        mlr_graph : str — Phase 1 MLR graph (for logging / analysis)
        """
        task = task_description.strip()

        # ── Phase 1: Enhanced MLR Graph ──────────────────────────────
        logger.debug("MoT+ Phase 1: generating enhanced MLR graph")
        mlr_graph = self._generate_mlr_graph(task)
        logger.debug("MLR graph: %d chars", len(mlr_graph))

        # ── Phase 2: Modular Code Generation ─────────────────────────
        logger.debug("MoT+ Phase 2: generating modular code")
        code = self._generate_code(task, mlr_graph, entry_point)

        # ── Phase 3: Execution-guided Self-repair ─────────────────────
        tests = self._collect_tests(task, entry_point)
        if tests:
            logger.debug("MoT+ Phase 3: %d tests available, starting repair loop", len(tests))
            code = self._repair_loop(task, mlr_graph, code, tests, entry_point)
        else:
            logger.debug("MoT+ Phase 3: no reliable tests found, skipping repair")

        return code, mlr_graph

    # ------------------------------------------------------------------
    # Phase 1
    # ------------------------------------------------------------------

    def _generate_mlr_graph(self, task: str) -> str:
        """Phase 1: use the paper-exact MoT MLR graph prompt."""
        user_msg = (
            f"Programming problem:\n{task.strip()}\n\n"
            "Generate the MLR Graph for this problem following the format above."
        )
        return self.llm.chat(
            [{"role": "user", "content": user_msg}],
            system=MLR_GRAPH_PROMPT,
        )

    # ------------------------------------------------------------------
    # Phase 2
    # ------------------------------------------------------------------

    def _generate_code(self, task: str, mlr_graph: str, entry_point: str) -> str:
        """Phase 2: use the paper-exact MoT code generation prompt."""
        user_content = (
            f"Programming problem:\n{task.strip()}\n\n"
            + CODE_GEN_PROMPT_TEMPLATE.format(mlr_graph=mlr_graph)
        )
        raw = self.llm.chat(
            [{"role": "user", "content": user_content}],
            system=CODE_GEN_SYSTEM,
        )
        return _extract_code(raw, entry_point)

    # ------------------------------------------------------------------
    # Phase 3 helpers
    # ------------------------------------------------------------------

    def _collect_tests(self, task: str, entry_point: str) -> List[str]:
        """
        Collect tests for the repair loop.

        Strategy:
        1. Parse doctest/assert examples from the task prompt.
        2. Only use repair if we have >= 2 diverse test cases — a single test
           causes overfitting (the repair optimizes for that one case and breaks
           others). This is especially important for MBPP which has only 1 assert.
        3. Do NOT supplement with LLM-generated tests (they are often wrong
           and corrupt the repair signal).
        """
        doctest_asserts = _doctest_to_asserts(task, entry_point)
        logger.debug("MoT+ Phase 3: %d doctest asserts extracted", len(doctest_asserts))

        # Only repair when we have at least 2 reliable tests to avoid overfitting
        if len(doctest_asserts) >= 2:
            return doctest_asserts[:self.n_tests]

        # Too few tests: skip repair (return empty to disable repair loop)
        return []

    def _generate_llm_tests(self, task: str, entry_point: str) -> List[str]:
        """Generate supplementary test cases using the LLM."""
        user_content = MOTPLUS_TEST_GEN_TEMPLATE.format(task=task, n=4)
        raw = self.llm.chat(
            [{"role": "user", "content": user_content}],
            system=MOTPLUS_TEST_GEN_SYSTEM,
        )
        return _parse_assert_lines(raw)[:4]

    def _repair_loop(
        self,
        task: str,
        mlr_graph: str,
        code: str,
        tests: List[str],
        entry_point: str,
    ) -> str:
        """Iteratively run tests and repair failures."""
        for rnd in range(self.max_repair_rounds):
            status, failed, errors = execute_code(code, tests, self.exec_timeout)
            if status == "pass":
                logger.debug(
                    "MoT+ Phase 3: all %d tests passed after %d repair(s)",
                    len(tests), rnd,
                )
                break
            logger.debug(
                "MoT+ Phase 3: repair %d/%d — %d/%d tests failed",
                rnd + 1, self.max_repair_rounds, len(failed), len(tests),
            )
            code = self._repair(task, mlr_graph, code, failed, errors, entry_point)

        return code

    def _repair(
        self,
        task: str,
        mlr_graph: str,
        code: str,
        failed_tests: List[str],
        error_details: List[str],
        entry_point: str,
    ) -> str:
        user_content = MOTPLUS_REPAIR_TEMPLATE.format(
            task=task,
            mlr_graph=mlr_graph,
            code=code,
            failed_tests="\n".join(failed_tests),
            error_details="\n".join(error_details),
        )
        raw = self.llm.chat(
            [{"role": "user", "content": user_content}],
            system=MOTPLUS_REPAIR_SYSTEM,
        )
        return _extract_code(raw, entry_point)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _doctest_to_asserts(task: str, entry_point: str) -> List[str]:
    """
    Extract reliable test cases from the task description, supporting:

    1. Python doctest format (HumanEval style):
       >>> func_name(arg1, arg2)
       expected_result
       → "assert func_name(arg1, arg2) == expected_result"

    2. Direct assert format (MBPP style):
       assert func_name(arg1, arg2) == expected

    3. Arrow notation (==> style in some HumanEval docstrings):
       func_name(arg1) ==> expected_result
       → "assert func_name(arg1) == expected_result"

    Returns a list of assert statement strings.
    """
    asserts: List[str] = []
    lines = task.splitlines()
    i = 0
    _ARROW_RE = re.compile(r'^(.+?)\s*==>\s*(.+)$')

    while i < len(lines):
        stripped = lines[i].strip()

        # Format 1: >>> doctest style
        m = re.match(r'^>>>\s+(.+)$', stripped)
        if m:
            call_expr = m.group(1).strip()
            if i + 1 < len(lines):
                next_stripped = lines[i + 1].strip()
                if (
                    next_stripped
                    and not next_stripped.startswith(">>>")
                    and not next_stripped.startswith("#")
                ):
                    expected = next_stripped
                    assert_stmt = f"assert {call_expr} == {expected}"
                    asserts.append(assert_stmt)
                    i += 2
                    continue

        # Format 2: direct assert statements (MBPP style)
        if stripped.startswith("assert ") and entry_point and entry_point in stripped:
            asserts.append(stripped)
            i += 1
            continue

        # Format 3: arrow notation (func(args) ==> result)
        if entry_point and entry_point in stripped:
            m2 = _ARROW_RE.match(stripped)
            if m2:
                call_expr = m2.group(1).strip()
                expected = m2.group(2).strip()
                # Only add if the call looks like a function call
                if '(' in call_expr and ')' in call_expr:
                    assert_stmt = f"assert {call_expr} == {expected}"
                    asserts.append(assert_stmt)

        i += 1
    return asserts


def _parse_assert_lines(raw: str) -> List[str]:
    """Extract 'assert ...' lines from an LLM response."""
    lines = raw.strip().splitlines()
    in_fence = False
    out: List[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if stripped.lower().startswith("assert "):
            out.append(stripped)
    return out
