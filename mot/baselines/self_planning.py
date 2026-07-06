"""
Self-Planning baseline for code generation.

Reference: Jiang et al., "Self-Planning Code Generation with Large Language
Models", ACM TOSEM 2024.

Two-call pipeline:
  1. LLM generates a step-by-step natural-language plan.
  2. LLM implements the plan as Python code.

The prompt templates follow the paper for fair comparison.
"""
from __future__ import annotations

from mot.llm import LLMClient
from mot.mot_engine import _extract_code
from mot.prompts import (
    SELF_PLANNING_PLAN_SYSTEM,
    SELF_PLANNING_PLAN_TEMPLATE,
    SELF_PLANNING_CODE_SYSTEM,
    SELF_PLANNING_CODE_TEMPLATE,
)


class SelfPlanning:
    """Self-Planning two-stage prompting baseline."""

    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm

    def generate(self, task_description: str, entry_point: str = "") -> str:
        """
        Generate code via: (1) plan generation → (2) plan execution.

        Returns the final Python code.
        """
        task = task_description.strip()

        # Stage 1: generate plan
        plan_user = SELF_PLANNING_PLAN_TEMPLATE.format(task=task)
        plan = self.llm.chat(
            [{"role": "user", "content": plan_user}],
            system=SELF_PLANNING_PLAN_SYSTEM,
        )

        # Stage 2: implement plan
        code_user = SELF_PLANNING_CODE_TEMPLATE.format(task=task, plan=plan)
        raw = self.llm.chat(
            [{"role": "user", "content": code_user}],
            system=SELF_PLANNING_CODE_SYSTEM,
        )
        return _extract_code(raw, entry_point)
