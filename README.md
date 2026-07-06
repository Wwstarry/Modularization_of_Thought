# MoT: Modularization-of-Thought Prompting for Effective Code Generation

<p align="center">
  <a href="https://arxiv.org/abs/2503.12483"><img src="https://img.shields.io/badge/arXiv-2503.12483-b31b1b.svg" alt="arXiv"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License: MIT"></a>
  <img src="https://img.shields.io/badge/Python-3.9%2B-blue.svg" alt="Python 3.9+">
  <img src="https://img.shields.io/badge/evalplus-✓-brightgreen.svg" alt="evalplus">
</p>

> **Modularization is Better: Effective Code Generation with Modular Prompting**  
> Ruwei Pan · Hongyu Zhang  
> Chongqing University, China  
> *ACM 2025 · arXiv:2503.12483*

---

## Overview

Large Language Models (LLMs) typically generate code via a **monolithic reasoning process** where all steps are linearly coupled, limiting their ability to decompose complex programming tasks.

**MoT (Modularization-of-Thought)** brings the modularization principle from software engineering into LLM prompting. It decomposes complex programming problems into a hierarchical **Multi-Level Reasoning (MLR) Graph**, then generates structured, modular code guided by this graph.

### Two-Phase Pipeline

```
Programming problem
        │
        ▼
┌───────────────────────────────────────┐
│  Phase 1: MLR Graph Generation        │
│                                       │
│  H1 [High-Level]: Solve the problem   │
│  ├── H1.1 [High-Level]: Sub-task 1    │
│  │   ├── I1.1 [Intermediate]: ...     │
│  │   └── I1.2 [Intermediate]: ...     │
│  └── H1.2 [High-Level]: Sub-task 2   │
│      └── D1.1 [Detailed]: pseudo-code │
│                                       │
│  Each node embeds:                    │
│    • Task Purpose                     │
│    • Decision Rationale               │
│    • Execution Strategy               │
└───────────────────────────────────────┘
        │  MLR Graph
        ▼
┌───────────────────────────────────────┐
│  Phase 2: Modular Code Generation     │
│                                       │
│  Generate Python code guided by       │
│  the MLR graph. Each node maps to     │
│  a modular helper function.           │
└───────────────────────────────────────┘
        │
        ▼
   Modular Python code
```

---

## Main Results

### Pass@1 (%) — GPT-4o-mini

| Method | HumanEval | HumanEval+ | HumanEval-ET | MBPP | MBPP+ | MBPP-ET |
|--------|-----------|------------|--------------|------|-------|---------|
| Zero-shot | 88.4 | 81.1 | 87.1 | 59.9 | 47.9 | 53.6 |
| Few-shot | 82.3 | 76.2 | 81.7 | 49.1 | 40.6 | 48.4 |
| CoT | 87.8 | 82.9 | 87.8 | 61.2 | 48.6 | 54.1 |
| Self-planning | 87.2 | 79.9 | 87.1 | 52.1 | 42.4 | 48.2 |
| SCoT | 86.6 | 78.7 | 86.0 | 63.9 | 51.4 | 55.6 |
| CodeCoT | 83.5 | 73.8 | 82.4 | 55.6 | 40.4 | 53.3 |
| **MoT (ours)** | **92.1** | **83.5** | **91.5** | **73.9** | **58.1** | **58.9** |

### Pass@1 (%) — DeepSeek-R1 (671B)

| Method | HumanEval | HumanEval+ | HumanEval-ET | MBPP | MBPP+ | MBPP-ET |
|--------|-----------|------------|--------------|------|-------|---------|
| Zero-shot | 93.3 | 87.8 | 92.7 | 69.4 | 57.6 | 64.0 |
| Few-shot | 84.7 | 79.9 | 84.1 | 69.4 | 57.6 | 64.6 |
| CoT | 92.6 | 88.2 | 73.5 | 59.9 | 44.4 | 51.9 |
| Self-planning | 85.4 | 79.3 | 85.3 | 68.4 | 55.4 | 65.5 |
| SCoT | 84.8 | 79.3 | 84.1 | 57.9 | 46.9 | 61.3 |
| CodeCoT | 66.5 | 60.4 | 65.9 | 69.2 | 56.6 | 64.5 |
| **MoT (ours)** | **95.1** | **88.4** | **94.5** | **74.9** | **60.4** | **68.0** |

---

## Quick Start

```bash
# 1. Clone and install
git clone https://github.com/panruwei/MoT.git
cd MoT
pip install -e .

# 2. Set your API key
export OPENAI_API_KEY="<your-key>"

# 3. Run MoT on HumanEval
python evaluate/run_humaneval.py \
    --method mot \
    --model gpt-4o-mini \
    --dataset humaneval \
    --output results/humaneval_mot_gpt4omini.jsonl

# 4. Evaluate Pass@1
python -m evalplus.evaluate \
    --dataset humaneval \
    --samples results/humaneval_mot_gpt4omini.jsonl
```

---

## Installation

**Requirements:** Python 3.9+, an OpenAI API key (for GPT-4o-mini) or DeepSeek API key (for DeepSeek-R1).

```bash
pip install -e .
# or
pip install -r requirements.txt
```

Verify:
```bash
python -c "from mot import MoTEngine, LLMClient; print('MoT ready')"
```

---

## Datasets

All benchmarks load automatically via [evalplus](https://github.com/evalplus/evalplus) on first use:

| Dataset | # Problems | Notes |
|---------|-----------|-------|
| HumanEval | 164 | OpenAI handcrafted Python problems |
| HumanEval+ | 164 | HumanEval with ≈80× more test cases |
| HumanEval-ET | 164 | Extended test coverage |
| MBPP | 399 | Google sanitized Python problems |
| MBPP+ | 399 | MBPP with ≈80× more test cases |
| MBPP-ET | 399 | Extended test coverage |

---

## Running Experiments

### MoT on a single dataset

```bash
# HumanEval
python evaluate/run_humaneval.py \
    --method mot \
    --backend openai \
    --model gpt-4o-mini \
    --dataset humaneval \
    --output results/humaneval_mot_gpt4omini.jsonl

# HumanEval+
python evaluate/run_humaneval.py \
    --method mot \
    --model gpt-4o-mini \
    --dataset humaneval_plus \
    --output results/humaneval_plus_mot_gpt4omini.jsonl

# MBPP
python evaluate/run_mbpp.py \
    --method mot \
    --model gpt-4o-mini \
    --dataset mbpp \
    --output results/mbpp_mot_gpt4omini.jsonl
```

### With DeepSeek-R1

```bash
export OPENAI_API_KEY="<your-deepseek-key>"

python evaluate/run_humaneval.py \
    --method mot \
    --backend openai \
    --model deepseek-reasoner \
    --base-url https://api.deepseek.com \
    --max-tokens 8192 \
    --dataset humaneval \
    --output results/humaneval_mot_deepseek.jsonl
```

### Evaluate Pass@1

```bash
# HumanEval
python -m evalplus.evaluate --dataset humaneval \
    --samples results/humaneval_mot_gpt4omini.jsonl

# MBPP
python -m evalplus.evaluate --dataset mbpp \
    --samples results/mbpp_mot_gpt4omini.jsonl
```

### Reproduce Table 1 (all methods × all datasets)

```bash
# GPT-4o-mini — Table 1 top half
python evaluate/run_all.py \
    --backend openai \
    --model gpt-4o-mini \
    --output-dir results/

# DeepSeek-R1 — Table 1 bottom half
python evaluate/run_all.py \
    --backend openai \
    --model deepseek-reasoner \
    --base-url https://api.deepseek.com \
    --output-dir results/deepseek/

# Or one-shot with the convenience script
bash scripts/reproduce_paper.sh
```

Resumption is automatic: re-running with the same `--output` path skips already-completed problems.

---

## Supported Methods

| `--method` | Description | Reference |
|-----------|-------------|-----------|
| `mot` | Modularization-of-Thought (this paper) | arXiv:2503.12483 |
| `zero_shot` | Direct zero-shot prompting | Chen et al., 2021 |
| `few_shot` | 2-shot in-context learning | Chen et al., 2021 |
| `cot` | Chain-of-Thought prompting | Wei et al., NeurIPS 2022 |
| `self_planning` | Plan-then-execute | Jiang et al., TOSEM 2024 |
| `scot` | Structured CoT (sequence / branch / loop) | Li et al., TOSEM 2023 |
| `codecot` | CoT + test generation + self-repair | Yao et al., EMNLP 2024 |

---

## Python API

```python
from mot import LLMClient, MoTEngine

llm = LLMClient(
    backend="openai",
    model="gpt-4o-mini",
    temperature=1.0,
)

engine = MoTEngine(llm)

task = '''
def has_close_elements(numbers: List[float], threshold: float) -> bool:
    """ Check if in given list of numbers, are any two numbers closer to each
    other than given threshold. """
'''

code, mlr_graph = engine.generate(task, entry_point="has_close_elements")

print("MLR Graph:")
print(mlr_graph)
print("\nGenerated Code:")
print(code)
```

---

## Project Structure

```
mot/
├── README.md
├── requirements.txt
├── pyproject.toml
│
├── mot/                     ← Core library
│   ├── llm.py               ← LLM client (OpenAI + Anthropic)
│   ├── executor.py          ← Sandboxed code executor
│   ├── prompts.py           ← Prompt templates (paper Figure 3)
│   ├── mot_engine.py        ← MoTEngine: Phase 1 + Phase 2
│   └── baselines/           ← Six baseline methods
│       ├── zero_shot.py
│       ├── few_shot.py
│       ├── cot.py
│       ├── self_planning.py
│       ├── scot.py
│       └── codecot.py
│
├── evaluate/
│   ├── run_humaneval.py     ← HumanEval / HumanEval+ evaluation
│   ├── run_mbpp.py          ← MBPP / MBPP+ evaluation
│   ├── run_all.py           ← Full Table 1 reproduction
│   └── metrics.py           ← Pass@1 and AvgPassRatio (APR)
│
├── configs/
│   ├── gpt4o_mini.yaml      ← GPT-4o-mini config
│   └── deepseek_r1.yaml     ← DeepSeek-R1 config
│
├── results/                 ← Output .jsonl files
└── scripts/
    ├── reproduce_paper.sh   ← One-shot Table 1 script
    └── eval_pass1.sh        ← Batch evalplus evaluation
```

---

## Ablation Study

The paper studies two MoT variants to validate each component (Table 2):

| Variant | HumanEval | MBPP |
|---------|-----------|------|
| w/o MLR Graph | 85.4 | 59.9 |
| w/o Modularization | 82.9 | 62.4 |
| **MoT (full)** | **92.1** | **73.9** |

*(GPT-4o-mini, Pass@1 %)*

---

## Citation

```bibtex
@article{pan2025mot,
  title   = {Modularization is Better: Effective Code Generation with Modular Prompting},
  author  = {Ruwei Pan and Hongyu Zhang},
  journal = {arXiv preprint arXiv:2503.12483},
  year    = {2025},
  url     = {https://arxiv.org/abs/2503.12483},
}
```

---

## License

This project is released under the [MIT License](LICENSE).

## Acknowledgements

We thank the developers of [evalplus](https://github.com/evalplus/evalplus) for providing a reliable evaluation framework for code generation benchmarks.
