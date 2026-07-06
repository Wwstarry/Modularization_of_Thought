"""
Prompt templates from the MoT paper (arXiv:2503.12483) and enhanced variants.

- Paper-exact templates: reproduced verbatim from Figure 3 of the paper.
- Enhanced templates (MLR_GRAPH_SYSTEM_PLUS, MLR_GRAPH_PROMPT_PLUS): add a
  concrete few-shot example of a high-quality MLR graph and more explicit node
  requirements, used by MoTPlus for improved performance.
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Phase 1: MLR Graph Generation  (paper-exact, verbatim from Figure 3)
# ---------------------------------------------------------------------------

MLR_GRAPH_SYSTEM = (
    "You are a code reasoning assistant. Your task is to analyze the given "
    "programming problem and generate a modular reasoning graph "
    "(Multi-Level Reasoning Graph, MLR Graph) to guide the code generation "
    "process. Provide your reasoning in the following hierarchical textual "
    "format clearly:"
)

MLR_GRAPH_FORMAT = """\
### Format
H1 [High-Level]: Solve the problem: {problem description}
Reasoning: Break the problem into major tasks: {High-level task 1} and {High-level task 2}.
├── H1.1 [High-Level]: {Subtask 1 of High-Level}
│   Reasoning: {Reasoning for subtask 1}
│   ├── I1.1 [Intermediate-Level]: {Intermediate-level task 1 for subtask 1}
│   │   Reasoning: {Reasoning for intermediate-level task 1}
│   └── I1.2 [Intermediate-Level]: {Intermediate-level task 2 for subtask 1}
│       Reasoning: {Reasoning for intermediate-level task 2}
├── H1.2 [High-Level]: {Subtask 2 of High-Level}
│   Reasoning: {Reasoning for subtask 2}
│   ├── I2.1 [Intermediate-Level]: {Intermediate-level task 1 for subtask 2}
│   │   Reasoning: {Reasoning for intermediate-level task 1}
│   │   └── D2.1 [Detailed-Level]: {Detailed implementation details or pseudo-code}"""

MLR_GRAPH_PROMPT = MLR_GRAPH_SYSTEM + "\n\n" + MLR_GRAPH_FORMAT

# ---------------------------------------------------------------------------
# Phase 1 ENHANCED: MLR Graph Generation with few-shot example + richer
# node requirements (used by MoTPlus for higher accuracy)
# ---------------------------------------------------------------------------

MLR_GRAPH_SYSTEM_PLUS = """\
You are an expert software engineer and code reasoning assistant. Your task is
to analyze the given programming problem and produce a clear Multi-Level
Reasoning Graph (MLR Graph) that will guide correct modular code generation.

Rules for a high-quality MLR Graph
────────────────────────────────────
1. High-Level (H) nodes define the PRIMARY algorithmic steps of the whole task.
2. Intermediate-Level (I) nodes refine each high-level task into concrete
   sub-steps (loop structures, condition handling, data transformations).
3. Detailed-Level (D) nodes give precise implementation details: exact data
   structures, Python built-ins to use, specific algorithm choices.
4. Every node must include Reasoning with three sub-elements:
   • Task Purpose  – WHY this step is needed
   • Decision Rationale – WHY this specific design choice (algorithm / data structure)
   • Execution Strategy – HOW to implement (pseudo-code, built-ins)
5. IMPORTANT: Follow the problem specification EXACTLY. Do NOT add extra input
   validation or raise exceptions unless the problem explicitly requires it.
   The function must produce exactly the outputs shown in the docstring examples.

──────────────────────────────────────
EXAMPLE (problem: "Given a list of lists and an integer K, find the largest
                   sum among the sub-lists and divide it by K.")
──────────────────────────────────────
H1 [High-Level]: Solve the problem
Reasoning:
  Task Purpose: Orchestrate the core algorithmic steps.
  Decision Rationale: Separate sum computation, max tracking, and final division.
  Execution Strategy: Call find_max_sum(array) → divide by K.
├── H1.1 [High-Level]: Compute the maximum sublist sum
│   Reasoning:
│     Task Purpose: Find the largest sum across all sub-lists.
│     Decision Rationale: Use Python built-in sum() for O(n) per sublist.
│     Execution Strategy: Iterate over sublists with a running max.
│   ├── I1.1 [Intermediate-Level]: Iterate over each sublist
│   │   Reasoning:
│   │     Task Purpose: Visit every sublist to compute its sum.
│   │     Decision Rationale: A simple for-loop is readable and O(n*m).
│   │     Execution Strategy: for sublist in array: current = sum(sublist)
│   └── I1.2 [Intermediate-Level]: Track running maximum
│       Reasoning:
│         Task Purpose: Maintain the largest sum seen so far.
│         Decision Rationale: Initialise with float('-inf') to handle all-negative lists.
│         Execution Strategy: max_sum = float('-inf'); max_sum = max(max_sum, current)
└── H1.2 [High-Level]: Return max_sum / K
    Reasoning:
      Task Purpose: Produce the final answer.
      Decision Rationale: True division (/) preserves float result.
      Execution Strategy: return max_sum / K
──────────────────────────────────────

Now produce the MLR Graph for the given problem following the exact same
structure and level of detail."""

MLR_GRAPH_PROMPT_PLUS = MLR_GRAPH_SYSTEM_PLUS  # single-block system prompt


# ---------------------------------------------------------------------------
# Phase 2: Code Generation
# ---------------------------------------------------------------------------

CODE_GEN_SYSTEM = (
    "You are a code generation assistant. Your task is to generate modular "
    "Python code based on the given modular reasoning (MLR graph). "
    "Rules:\n"
    "- Output ONLY executable Python code. No prose, no markdown fences.\n"
    "- Do NOT include print(), assert, or test statements.\n"
    "- Do NOT add input validation or raise exceptions unless the docstring requires it.\n"
    "- Use ONLY Python standard library (math, re, collections, itertools, typing, heapq, etc.).\n"
    "  NEVER import scipy, numpy, pandas, sympy, or any third-party library.\n"
    "- Include all necessary standard-library imports at the top.\n"
    "- Implement the function specified in the docstring so it matches the examples exactly.\n"
    "- Organize code into helper functions guided by the MLR graph."
)

CODE_GEN_PROMPT_TEMPLATE = """\
Modular Reasoning (MLR graph):
{mlr_graph}

Output the complete Python implementation (no explanations, no tests):"""

# Enhanced code generation system prompt (used by MoTPlus)
CODE_GEN_SYSTEM_PLUS = """\
You are an expert Python programmer. Generate correct, modular Python code
guided by the provided MLR graph. Requirements:
- Implement key algorithmic steps as separate helper functions when appropriate.
- The entry-point function must implement the exact specification in the docstring.
- Do NOT add extra input validation or raise exceptions unless explicitly stated
  in the problem — this will cause test failures.
- Add necessary imports (typing, math, collections, etc.) at the top.
- The function must pass the docstring examples exactly.
- Output ONLY the complete Python code — no explanations, no markdown fences."""

CODE_GEN_PROMPT_TEMPLATE_PLUS = """\
Programming problem:
{task}

MLR Graph (use this to guide your implementation):
{mlr_graph}

Implement the complete, correct Python solution.
Follow the problem docstring exactly — do not add extra validations.
Output only the Python code:"""

# ---------------------------------------------------------------------------
# MoT+ Phase 3: Execution-guided repair
# ---------------------------------------------------------------------------

MOTPLUS_REPAIR_SYSTEM = """\
You are an expert Python debugger. Fix the provided code so it passes the
failing tests. Follow these rules:
- Produce the EXACT outputs shown in the docstring for the given inputs.
- Do NOT add extra input validation or raise exceptions not asked for.
- Do NOT add unnecessary type checks — trust the problem specification.
- Keep the modular structure but fix the algorithmic logic.
- Output ONLY the corrected, complete Python code."""

MOTPLUS_REPAIR_TEMPLATE = """\
Programming problem:
{task}

Current code (incorrect):
{code}

Failing tests and errors:
{failed_tests}
---
{error_details}

Fix ONLY the algorithmic bug. Do not add extra validation.
Output only the corrected Python code:"""

# MoT+ test generation prompt
MOTPLUS_TEST_GEN_SYSTEM = """\
You are a Python test engineer. Given a programming problem and its function
signature, generate diverse Python assert statements to test the implementation.
Cover: typical cases, edge cases (empty inputs, single element, negatives,
large values, type boundaries). Output ONLY assert statements, one per line."""

MOTPLUS_TEST_GEN_TEMPLATE = """\
Programming problem:
{task}

Generate {n} assert-based test cases covering diverse scenarios:"""


# ---------------------------------------------------------------------------
# Baseline: Zero-shot
# ---------------------------------------------------------------------------

ZERO_SHOT_SYSTEM = (
    "You are a Python programming assistant. "
    "Generate a complete, correct Python function for the given problem. "
    "Output only the code, no explanation."
)

ZERO_SHOT_PROMPT_TEMPLATE = "{task}"


# ---------------------------------------------------------------------------
# Baseline: Few-shot (2-shot with canonical HumanEval examples)
# ---------------------------------------------------------------------------

FEW_SHOT_SYSTEM = (
    "You are a Python programming assistant. "
    "Study the examples below, then generate a complete Python function "
    "for the new problem. Output only the code."
)

FEW_SHOT_EXAMPLES = '''\
Example 1:
def has_close_elements(numbers: List[float], threshold: float) -> bool:
    """ Check if in given list of numbers, are any two numbers closer to each other than
    given threshold.
    >>> has_close_elements([1.0, 2.0, 3.0], 0.5)
    False
    >>> has_close_elements([1.0, 2.8, 3.0, 4.0, 5.0, 2.0], 0.3)
    True
    """
    for idx, elem in enumerate(numbers):
        for idx2, elem2 in enumerate(numbers):
            if idx != idx2:
                distance = abs(elem - elem2)
                if distance < threshold:
                    return True
    return False

Example 2:
def separate_paren_groups(paren_string: str) -> List[str]:
    """ Input to this function is a string containing multiple groups of nested parentheses.
    Your goal is to separate those group into separate strings and return the list of those.
    Separate groups are balanced (each open brace is properly closed) and not nested within
    each other. Ignore any spaces in the input string.
    >>> separate_paren_groups('( ) (( )) (( )( ))')
    ['()', '(())', '(()())']
    """
    result = []
    current_string = []
    current_depth = 0
    for c in paren_string:
        if c == '(':
            current_depth += 1
            current_string.append(c)
        elif c == ')':
            current_depth -= 1
            current_string.append(c)
            if current_depth == 0:
                result.append(''.join(current_string))
                current_string = []
    return result

New problem:
{task}'''

FEW_SHOT_PROMPT_TEMPLATE = FEW_SHOT_EXAMPLES


# ---------------------------------------------------------------------------
# Baseline: Chain-of-Thought (CoT)
# ---------------------------------------------------------------------------

COT_SYSTEM = (
    "You are a Python programming assistant. "
    "Think step by step about the problem before writing the code. "
    "After your reasoning, output the complete Python function. "
    "Wrap the final code in ```python ... ``` markers."
)

COT_PROMPT_TEMPLATE = "{task}"


# ---------------------------------------------------------------------------
# Baseline: Self-Planning
# ---------------------------------------------------------------------------

SELF_PLANNING_PLAN_SYSTEM = (
    "You are a Python programming assistant. "
    "First, create a detailed, step-by-step plan for solving the given "
    "programming problem. Do not write code yet — only the plan."
)

SELF_PLANNING_PLAN_TEMPLATE = "{task}"

SELF_PLANNING_CODE_SYSTEM = (
    "You are a Python programming assistant. "
    "Based on the plan provided, implement the complete Python function. "
    "Output only the final code."
)

SELF_PLANNING_CODE_TEMPLATE = """\
Problem:
{task}

Plan:
{plan}

Now implement the Python function following the plan exactly."""


# ---------------------------------------------------------------------------
# Baseline: SCoT (Structured Chain-of-Thought)
# ---------------------------------------------------------------------------

SCOT_SYSTEM = (
    "You are a Python programming assistant. "
    "Use program structures (sequence, branch, and loop) to guide your "
    "reasoning. First describe the structure of your solution using these "
    "building blocks, then implement the complete Python function. "
    "Wrap the final code in ```python ... ``` markers."
)

SCOT_PROMPT_TEMPLATE = """\
Programming problem:
{task}

Describe the solution structure using:
- SEQUENCE: steps executed one after another
- BRANCH: if/else conditions
- LOOP: for/while iterations

Then write the complete implementation."""


# ---------------------------------------------------------------------------
# Baseline: CodeCoT (CoT + test generation + self-repair)
# ---------------------------------------------------------------------------

CODECOT_INITIAL_CODE_SYSTEM = (
    "You are a Python programming assistant. "
    "Think step by step, then write a complete Python function. "
    "Wrap the final code in ```python ... ``` markers."
)

CODECOT_INITIAL_CODE_TEMPLATE = "{task}"

CODECOT_TEST_GEN_SYSTEM = (
    "You are a test-case generation assistant. "
    "Generate Python assert statements to test the given function. "
    "Output only the assert statements, one per line."
)

CODECOT_TEST_GEN_TEMPLATE = """\
Generate 5 assert-based test cases for the following Python function:

{task}

Output only Python assert statements (no imports, no def statements):"""

CODECOT_REPAIR_SYSTEM = (
    "You are a Python code repair assistant. "
    "Fix the provided code so it passes all the failing tests. "
    "Output only the corrected, complete Python function."
)

CODECOT_REPAIR_TEMPLATE = """\
The following Python code has errors. Fix it.

Code:
{code}

Failing tests:
{failed_tests}

Error details:
{error_details}

Output only the corrected code:"""
