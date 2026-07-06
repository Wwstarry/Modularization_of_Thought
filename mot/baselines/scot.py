"""
SCoT (Structured Chain-of-Thought) baseline for code generation.

Reference: Li et al., "Structured Chain-of-Thought Prompting for Code
Generation", ACM TOSEM 2023.

Extends CoT by leveraging three fundamental program structures — sequence,
branch (if/else), and loop (for/while) — to generate structured intermediate
reasoning steps that align more closely with actual programming logic.

The prompt template follows the paper for fair comparison.
"""
from __future__ import annotations

from mot.llm import LLMClient
from mot.mot_engine import _extract_code
from mot.prompts import SCOT_SYSTEM, SCOT_PROMPT_TEMPLATE


class SCoT:
    """Structured Chain-of-Thought prompting baseline."""

    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm

    def generate(self, task_description: str, entry_point: str = "") -> str:
        """
        Generate code using program-structure-guided reasoning.

        The LLM first describes the solution structure (SEQUENCE / BRANCH / LOOP),
        then writes the full implementation.
        """
        user_content = SCOT_PROMPT_TEMPLATE.format(task=task_description.strip())
        messages = [{"role": "user", "content": user_content}]
        raw = self.llm.chat(messages, system=SCOT_SYSTEM)
        return _extract_code(raw, entry_point)
