"""
MoT-SC+ (Self-Consistency + Repair): best-of-N selection followed by repair.

Pipeline:
  1. Generate N independent MoT solutions.
  2. Select the solution that passes the most doctest examples (oracle).
  3. If the selected solution fails any doctests, run the repair loop.

This combines the diversity of sampling with the precision of repair.
"""
from __future__ import annotations

import logging
from typing import List, Tuple

from mot.executor import count_passed, execute_code
from mot.llm import LLMClient
from mot.mot_engine import MoTEngine, _extract_code
from mot.mot_plus import MoTPlusEngine, _doctest_to_asserts, _parse_assert_lines
from mot.prompts import MOTPLUS_REPAIR_SYSTEM, MOTPLUS_REPAIR_TEMPLATE

logger = logging.getLogger(__name__)

_DEFAULT_N_SAMPLES = 3
_DEFAULT_MAX_REPAIR_ROUNDS = 2
_DEFAULT_EXEC_TIMEOUT = 30


class MoTSCPlusEngine:
    """
    MoT-SC+ = best-of-N selection + repair loop.

    Parameters
    ----------
    llm : LLMClient
    n_samples : int    Number of independent MoT samples (default: 3).
    max_repair_rounds : int   Repair iterations (default: 2).
    exec_timeout : int   Code execution timeout (default: 30).
    """

    def __init__(
        self,
        llm: LLMClient,
        n_samples: int = _DEFAULT_N_SAMPLES,
        max_repair_rounds: int = _DEFAULT_MAX_REPAIR_ROUNDS,
        exec_timeout: int = _DEFAULT_EXEC_TIMEOUT,
    ) -> None:
        self.llm = llm
        self.n_samples = n_samples
        self.max_repair_rounds = max_repair_rounds
        self.exec_timeout = exec_timeout
        self._mot = MoTEngine(llm)

    def generate(
        self,
        task_description: str,
        entry_point: str = "",
    ) -> Tuple[str, str]:
        task = task_description.strip()
        doctests = _doctest_to_asserts(task, entry_point)

        # Step 1: Sample N MoT solutions
        solutions: List[Tuple[str, str]] = []
        for i in range(self.n_samples):
            try:
                code, mlr = self._mot.generate(task, entry_point)
                solutions.append((code, mlr))
                # Early exit: if this solution already passes all doctests
                if doctests:
                    status, _, _ = execute_code(code, doctests, self.exec_timeout)
                    if status == "pass":
                        logger.debug("MoT-SC+: sample %d passes all doctests — early exit", i + 1)
                        return code, mlr
            except Exception as exc:
                logger.warning("MoT-SC+: sample %d failed: %s", i + 1, exc)

        if not solutions:
            raise RuntimeError("MoT-SC+: all samples failed")

        # Step 2: Select best solution by doctest score
        if doctests:
            best_code, best_mlr = max(
                solutions,
                key=lambda s: count_passed(s[0], doctests, self.exec_timeout),
            )
        else:
            best_code, best_mlr = solutions[0]

        # Step 3: Repair the selected solution if it fails doctests
        if doctests:
            best_code = self._repair_loop(task, best_mlr, best_code, doctests, entry_point)

        return best_code, best_mlr

    def _repair_loop(
        self,
        task: str,
        mlr_graph: str,
        code: str,
        tests: List[str],
        entry_point: str,
    ) -> str:
        for rnd in range(self.max_repair_rounds):
            status, failed, errors = execute_code(code, tests, self.exec_timeout)
            if status == "pass":
                logger.debug("MoT-SC+: repaired after %d round(s)", rnd)
                break
            user_content = MOTPLUS_REPAIR_TEMPLATE.format(
                task=task,
                mlr_graph=mlr_graph,
                code=code,
                failed_tests="\n".join(failed),
                error_details="\n".join(errors),
            )
            raw = self.llm.chat(
                [{"role": "user", "content": user_content}],
                system=MOTPLUS_REPAIR_SYSTEM,
            )
            code = _extract_code(raw, entry_point)
        return code
