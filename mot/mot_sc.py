"""
MoT-SC (MoT with Self-Consistency / Best-of-N selection).

Generates N independent MoT solutions and selects the best one via:
  1. First try: return the first solution that passes all doctest examples.
  2. Fallback: return the solution that passes the most doctest examples.
  3. Final fallback: return the first solution.

This dramatically increases pass@1 by effectively running pass@N with an
oracle that uses the docstring examples as a selection signal.

N=3 is usually sufficient: theoretical improvement ≈ 1-(1-p)^N.
  If single-shot pass@1 = 83.5% (our baseline), then:
    N=2: 1-(1-0.835)^2 = 97.3% theoretical upper bound
    N=3: 1-(1-0.835)^3 = 99.5% theoretical upper bound
  In practice (not all failures are independent) the gain is lower but
  still substantial.
"""
from __future__ import annotations

import logging
from typing import List, Optional, Tuple

from mot.executor import count_passed, execute_code
from mot.llm import LLMClient
from mot.mot_engine import MoTEngine, _extract_code
from mot.mot_plus import _doctest_to_asserts

logger = logging.getLogger(__name__)

_DEFAULT_N_SAMPLES = 3
_DEFAULT_EXEC_TIMEOUT = 30


class MoTSCEngine:
    """
    MoT with Self-Consistency: sample N times, pick the best solution.

    Parameters
    ----------
    llm : LLMClient
    n_samples : int
        Number of independent MoT solutions to generate (default: 3).
    exec_timeout : int
        Code execution timeout per test, in seconds (default: 30).
    """

    def __init__(
        self,
        llm: LLMClient,
        n_samples: int = _DEFAULT_N_SAMPLES,
        exec_timeout: int = _DEFAULT_EXEC_TIMEOUT,
    ) -> None:
        self.llm = llm
        self.n_samples = n_samples
        self.exec_timeout = exec_timeout
        self._engine = MoTEngine(llm)

    # ------------------------------------------------------------------
    # Public API (same interface as MoTEngine / MoTPlusEngine)
    # ------------------------------------------------------------------

    def generate(
        self,
        task_description: str,
        entry_point: str = "",
    ) -> Tuple[str, str]:
        """
        Generate N MoT solutions, return the best one.

        Returns
        -------
        best_code : str
        mlr_graph : str — from the first sample (for logging)
        """
        task = task_description.strip()
        doctest_asserts = _doctest_to_asserts(task, entry_point)

        solutions: List[Tuple[str, str]] = []  # (code, mlr_graph)

        for i in range(self.n_samples):
            logger.debug("MoT-SC: sample %d/%d", i + 1, self.n_samples)
            try:
                code, mlr_graph = self._engine.generate(task, entry_point)
                solutions.append((code, mlr_graph))

                if doctest_asserts:
                    status, _, _ = execute_code(code, doctest_asserts, self.exec_timeout)
                    if status == "pass":
                        logger.debug("MoT-SC: sample %d passes all doctests — early exit", i + 1)
                        return code, mlr_graph
            except Exception as exc:
                logger.warning("MoT-SC: sample %d failed: %s", i + 1, exc)

        if not solutions:
            raise RuntimeError("MoT-SC: all samples failed")

        if not doctest_asserts:
            # No doctests to rank by — return first solution
            return solutions[0]

        # Pick solution with highest doctest pass count
        best_code, best_mlr = max(
            solutions,
            key=lambda s: count_passed(s[0], doctest_asserts, self.exec_timeout),
        )
        logger.debug("MoT-SC: selected best-of-%d by doctest pass count", len(solutions))
        return best_code, best_mlr
