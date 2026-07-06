"""
MoT (Modularization-of-Thought) Engine.

Implements Algorithm 1 from the paper:
  "Modularization is Better: Effective Code Generation with Modular Prompting"
  Ruwei Pan & Hongyu Zhang, arXiv:2503.12483

Two-phase pipeline
------------------
Phase 1: MLR Graph Generation
  - Parse the task description
  - Construct a Multi-Level Reasoning (MLR) Graph with three hierarchical
    levels: High-Level (H), Intermediate-Level (I), Detailed-Level (D)
  - Each node embeds: Task Purpose, Decision Rationale, Execution Strategy

Phase 2: Modular Code Generation
  - Feed the MLR graph into the LLM
  - Generate modular, hierarchically structured Python code
"""
from __future__ import annotations

import re
import logging
from typing import Tuple

from mot.llm import LLMClient
from mot.prompts import (
    MLR_GRAPH_PROMPT,
    CODE_GEN_SYSTEM,
    CODE_GEN_PROMPT_TEMPLATE,
)

logger = logging.getLogger(__name__)


class MoTEngine:
    """
    Two-phase MoT prompting engine.

    Parameters
    ----------
    llm : LLMClient
        Pre-configured LLM backend (OpenAI or Anthropic).
    """

    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(
        self,
        task_description: str,
        entry_point: str = "",
    ) -> Tuple[str, str]:
        """
        Run the full MoT pipeline on a single programming problem.

        Parameters
        ----------
        task_description : str
            The natural-language + function signature problem description
            (e.g. the full HumanEval prompt including docstring).
        entry_point : str
            The name of the function to be implemented. Used to clean up
            the generated code when the LLM outputs extra scaffolding.

        Returns
        -------
        code : str
            The generated Python code (complete, executable).
        mlr_graph : str
            The MLR graph produced in Phase 1 (for logging / analysis).
        """
        # Phase 1 — MLR Graph Generation
        logger.debug("Phase 1: generating MLR graph")
        mlr_graph = self._generate_mlr_graph(task_description)
        logger.debug("MLR graph generated (%d chars)", len(mlr_graph))

        # Phase 2 — Modular Code Generation
        logger.debug("Phase 2: generating code from MLR graph")
        code = self._generate_code(task_description, mlr_graph, entry_point)
        logger.debug("Code generated (%d chars)", len(code))

        return code, mlr_graph

    # ------------------------------------------------------------------
    # Phase 1
    # ------------------------------------------------------------------

    def _generate_mlr_graph(self, task: str) -> str:
        """Generate the MLR graph for *task* using the paper's prompt."""
        # If there are doctest examples, first verify the algorithm by tracing
        # through them. This prevents incorrect edge-case handling.
        doctest_examples = _extract_doctest_examples(task)
        if doctest_examples:
            trace_msg = (
                f"Programming problem:\n{task.strip()}\n\n"
                "Before generating the MLR Graph, trace through each example "
                "step-by-step to verify the exact algorithm:\n"
                + doctest_examples
                + "\n\nFor each example, show:"
                "\n  - What specific values/indices/steps lead to the output"
                "\n  - Any edge cases (empty inputs, duplicates, boundary values)"
                "\n  - The exact algorithm rule that produces the correct result"
                "\n\nThen generate the MLR Graph with the verified algorithm:"
            )
        else:
            trace_msg = (
                f"Programming problem:\n{task.strip()}\n\n"
                "Generate the MLR Graph for this problem following the format above."
            )

        messages = [{"role": "user", "content": trace_msg}]
        raw = self.llm.chat(messages, system=MLR_GRAPH_PROMPT)
        # Extract just the MLR graph portion (starting from first H1 node)
        mlr_graph = _extract_mlr_graph(raw)
        return mlr_graph

    # ------------------------------------------------------------------
    # Phase 2
    # ------------------------------------------------------------------

    def _generate_code(
        self,
        task: str,
        mlr_graph: str,
        entry_point: str,
    ) -> str:
        """Generate modular code guided by *mlr_graph*."""
        user_content = (
            f"Programming problem:\n{task.strip()}\n\n"
            + CODE_GEN_PROMPT_TEMPLATE.format(mlr_graph=mlr_graph)
        )
        # Add explicit verification targets from doctest examples if available
        doctest_hint = _extract_doctest_examples(task)
        if doctest_hint:
            user_content += (
                "\n\nVerify your implementation produces exactly these outputs:\n"
                + doctest_hint
            )
        messages = [{"role": "user", "content": user_content}]
        raw = self.llm.chat(messages, system=CODE_GEN_SYSTEM)
        code = _extract_code(raw, entry_point)
        code = _clean_trailing_noise(code)
        return code


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _extract_mlr_graph(raw: str) -> str:
    """
    Extract the MLR graph portion from Phase 1's full response.

    When Phase 1 includes a doctest trace followed by the MLR graph,
    this finds the first "H1 [High-Level]:" line and returns from there.
    Falls back to the full response if no H1 marker is found.
    """
    lines = raw.splitlines()
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("H1 [High-Level]") or stripped.startswith("H1 [high-level]"):
            return "\n".join(lines[i:]).strip()
    return raw.strip()


def _extract_doctest_examples(task: str) -> str:
    """
    Extract Python doctest-style examples from the task prompt and format them
    as a simple list for inclusion in the code generation prompt.

    E.g.: ">>> median([3,1,2]) == 3\n>>> median([1,2]) == 1.5"
    """
    lines = task.splitlines()
    pairs = []
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        m = re.match(r'^>>>\s+(.+)$', stripped)
        if m:
            call = m.group(1).strip()
            if i + 1 < len(lines):
                nxt = lines[i + 1].strip()
                if nxt and not nxt.startswith(">>>") and not nxt.startswith("#"):
                    pairs.append(f"  {call} → {nxt}")
                    i += 2
                    continue
        i += 1
    return "\n".join(pairs)


# ---------------------------------------------------------------------------
# Helper: code extraction
# ---------------------------------------------------------------------------


def _extract_code(raw: str, entry_point: str = "") -> str:
    """
    Extract the Python code block from the LLM response.

    Strategy (in order):
    1. Unwrap a ```python ... ``` fenced block (closing fence optional — handles
       responses truncated at max_tokens boundary).
    2. Unwrap a plain ``` ... ``` block (same).
    3. Scan the whole response for the first unambiguous Python statement.
    4. Fallback: return the full response (trimmed).

    After any extraction, ``_trim_to_code_start`` strips leading prose lines
    that the model may have injected inside the code block.
    """
    # Strategy 1: fenced python block (closing fence optional)
    m = re.search(r"```python\s*\n(.*?)(?:```|$)", raw, re.DOTALL | re.IGNORECASE)
    if m:
        content = m.group(1).strip()
        if content:
            return _trim_to_code_start(content)

    # Strategy 2: any fenced block (closing fence optional)
    m = re.search(r"```(?:\w+)?\s*\n(.*?)(?:```|$)", raw, re.DOTALL)
    if m:
        content = m.group(1).strip()
        if content:
            return _trim_to_code_start(content)

    # Strategy 3: scan for unambiguous Python code lines in raw text
    return _trim_to_code_start(raw)


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------

_IMPORT_RE = re.compile(r"^(?:from\s+[\w.]+\s+import|import\s+[\w., ]+)")

# Lines that are clearly test/debug noise and not part of the solution
_NOISE_LINE_RE = re.compile(
    r"^(?:"
    r"print\s*\("           # print(...)
    r"|assert\s+"           # assert ...
    r"|#\s*(?:test|example|usage|output|result|expected)"  # # test...
    r"|if\s+__name__\s*==\s*['\"]__main__['\"]"           # if __name__ == ...
    r"|run_tests\s*\("      # run_tests()
    r"|test_\w+\s*\("       # test_foo()
    r")",
    re.IGNORECASE,
)


def _clean_trailing_noise(code: str) -> str:
    """
    Remove trailing blocks of print/assert/test code that the model appends
    after the actual solution. Preserves any noise lines that appear BEFORE
    the last function definition (they might be inline examples in docstrings).

    Strategy: find the last top-level function/class definition, then drop any
    trailing lines that are pure noise (print, assert, test invocations) after
    the last meaningful code statement at the top level.
    """
    lines = code.splitlines()

    # Find the last top-level definition
    last_def = -1
    for i, line in enumerate(lines):
        stripped = line.strip()
        if (
            (stripped.startswith("def ") or stripped.startswith("class "))
            and not line.startswith(" ")
            and not line.startswith("\t")
        ):
            last_def = i

    if last_def == -1:
        return code  # No function found — don't touch

    # Scan backwards from the end; remove trailing noise lines
    end = len(lines)
    for i in range(len(lines) - 1, last_def, -1):
        stripped = lines[i].strip()
        if not stripped:
            continue
        if _NOISE_LINE_RE.match(stripped):
            end = i
        else:
            break  # Stop at first non-noise line from the bottom

    return "\n".join(lines[:end]).rstrip()


def _trim_to_code_start(text: str) -> str:
    """
    Given a (possibly mixed) text, find the first line that looks like an
    unambiguous Python statement and return everything from there onward.

    Handles cases where the LLM writes prose inside a fenced code block,
    e.g. "from two integers, round it away..." before the actual code.
    """
    lines = text.splitlines()
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        # Unambiguous Python code starters
        if stripped.startswith("def ") or stripped.startswith("class "):
            return "\n".join(lines[i:]).strip()
        if _IMPORT_RE.match(stripped):
            return "\n".join(lines[i:]).strip()
        # Decorator — also unambiguous
        if stripped.startswith("@") and not stripped.startswith("@property"):
            return "\n".join(lines[i:]).strip()

    # No unambiguous code start found — return trimmed text as-is
    return text.strip()
