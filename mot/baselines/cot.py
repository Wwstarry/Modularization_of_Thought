"""
Chain-of-Thought (CoT) baseline for code generation.

Reference: Wei et al., "Chain-of-Thought Prompting Elicits Reasoning in
Large Language Models", NeurIPS 2022.

Prompts the LLM to produce a step-by-step reasoning trace before writing
the final code. The prompt used here follows the template adopted in the
MoT paper for fair comparison.
"""
from __future__ import annotations

from mot.llm import LLMClient
from mot.mot_engine import _extract_code
from mot.prompts import COT_SYSTEM, COT_PROMPT_TEMPLATE


class CoT:
    """Chain-of-Thought prompting baseline."""

    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm

    def generate(self, task_description: str, entry_point: str = "") -> str:
        """Generate code with step-by-step reasoning."""
        user_content = COT_PROMPT_TEMPLATE.format(task=task_description.strip())
        messages = [{"role": "user", "content": user_content}]
        raw = self.llm.chat(messages, system=COT_SYSTEM)
        return _extract_code(raw, entry_point)
