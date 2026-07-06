"""
Zero-shot baseline for code generation.

Sends the task description directly to the LLM without any examples
or intermediate reasoning, using only a minimal system prompt.
"""
from __future__ import annotations

from mot.llm import LLMClient
from mot.mot_engine import _extract_code
from mot.prompts import ZERO_SHOT_SYSTEM, ZERO_SHOT_PROMPT_TEMPLATE


class ZeroShot:
    """Zero-shot prompting baseline."""

    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm

    def generate(self, task_description: str, entry_point: str = "") -> str:
        """Generate code directly from the task description."""
        user_content = ZERO_SHOT_PROMPT_TEMPLATE.format(task=task_description.strip())
        messages = [{"role": "user", "content": user_content}]
        raw = self.llm.chat(messages, system=ZERO_SHOT_SYSTEM)
        return _extract_code(raw, entry_point)
