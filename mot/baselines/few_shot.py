"""
Few-shot (2-shot) baseline for code generation.

Prepends two canonical HumanEval examples (from the EvalPlus dataset) to
the task description. The paper uses the 2-shot setting.
"""
from __future__ import annotations

from mot.llm import LLMClient
from mot.mot_engine import _extract_code
from mot.prompts import FEW_SHOT_SYSTEM, FEW_SHOT_PROMPT_TEMPLATE


class FewShot:
    """2-shot prompting baseline using HumanEval canonical examples."""

    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm

    def generate(self, task_description: str, entry_point: str = "") -> str:
        """Generate code using 2-shot examples prepended to the task."""
        user_content = FEW_SHOT_PROMPT_TEMPLATE.format(task=task_description.strip())
        messages = [{"role": "user", "content": user_content}]
        raw = self.llm.chat(messages, system=FEW_SHOT_SYSTEM)
        return _extract_code(raw, entry_point)
