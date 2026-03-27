# Modularization-of-Thought Prompting for Effective Code Generation

## Introduction

This repository contains the implementation of our paper:

**"Modularization-of-Thought Prompting for Effective Code Generation"**

MoT is a planning-first prompting framework for code generation. It introduces a **Multi-Level Reasoning (MLR) Graph** as an intermediate representation between task decomposition and code generation, with the goal of improving the alignment between reasoning structure and generated code.

Our main contributions are as follows:

- **MoT prompting.** We propose a prompting framework that incorporates modularization principles from software development into the reasoning process of code generation.
- **MLR Graph.** We design a fixed-depth **Multi-Level Reasoning Graph** to structure hierarchical planning and improve reasoning-code alignment.
- **Comprehensive evaluation.** We evaluate MoT on multiple benchmarks and compare it with a diverse set of prompting and structured reasoning baselines.

The MoT prompt template is provided in `prompting_techniques/MoT.py`.


---

## Installation

Our code is implemented in Python and tested on Linux.

### Prerequisites

- Python >= 3.8

### Setup

Clone the repository and install dependencies:

```bash
git clone https://github.com/our_repo.git
cd Pass@1/evaluation
pip install -r requirements.txt
```

---

## Project Structure

The repository is organized as follows:

```text
📂 Modularization_of_Thought
├── 📂 APR
│   ├── APR_HumanEval+.py
│   ├── APR_HumanEval.py
│   ├── APR_HumanEval_ET.py
│   ├── APR_MBPP+.py
│   ├── APR_MBPP.py
│   └── APR_MBPP_ET.py
│
├── 📂 Dataset
│   ├── HumanEval+.jsonl
│   ├── HumanEval-ET.jsonl
│   ├── HumanEval-ET.jsonl.gz
│   ├── HumanEval.jsonl
│   ├── MBPP-ET.jsonl.gz
│   ├── MBPP_ET.jsonl
│   ├── MBPP_sanitized.jsonl
│   ├── MBPP_sanitized.jsonl.gz
│   ├── Mbpp+.jsonl
│   └── humaneval.jsonl
│
├── 📂 Pass@1
│   ├── 📂 evaluation
│   │   ├── __init__.py
│   │   ├── data.py
│   │   ├── evaluate_functional_correctness.py
│   │   ├── evaluation.py
│   │   └── execution.py
│   ├── requirements.txt
│   └── setup.py
│
├── 📂 experiments
│   ├── 📂 RQ1
│   │   ├── 📂 HumanEval_deepseek
│   │   ├── 📂 HumanEval_gpt-4o-mini
│   │   ├── 📂 MBPP_deepseek
│   │   └── 📂 MBPP_gpt-4o-mini
│   └── 📂 RQ2
│
├── 📂 prompting_techniques
├── 📂 tools
└── README.md
```

### Key Directories

- **`APR/`**: Automated program repair scripts for different datasets.
- **`Dataset/`**: Datasets used in evaluation.
- **`Pass@1/`**: Evaluation code for pass@1 and functional correctness.
  - **`evaluation/`**: Core evaluation scripts.
- **`experiments/`**: Experimental results and analysis.
- **`prompting_techniques/`**: Implementations of prompting strategies.
- **`tools/`**: Utility scripts for data processing and experiment management.

### Prompting Baselines Included

- **Zero-shot prompting**: Generates code directly from the problem description.
- **Few-shot prompting**: Uses a small number of in-context examples.
- **Chain-of-Thought (CoT)**: Uses step-by-step reasoning before generation.
- **Self-Planning**: Generates an explicit plan before coding.
- **SCoT**: Incorporates more structured program-oriented reasoning.
- **CodeCoT**: Combines reasoning with code-focused self-checking.

---

## Additional Results

### 1. Repository-Level Code Generation

To evaluate whether MoT transfers beyond function-level tasks, we additionally test it on two repository-level benchmarks: **NL2Repo-Bench** and **RAL-Bench**. In both settings, **MoT achieves the best overall performance** among the compared methods.

#### NL2Repo-Bench (GPT-5)

| Method | Overall Score | Easy | Medium | Hard |
| --- | ---: | ---: | ---: | ---: |
| Direct | 21.7 | 38.4 | 20.7 | 9.6 |
| Self-Reflection | 24.7 | 40.9 | 24.5 | 12.1 |
| SE-Agent | 25.4 | 44.5 | 23.6 | 12.6 |
| AlphaEvolve | 25.1 | 41.8 | 25.1 | 11.7 |
| CSE | 19.7 | 41.1 | 15.8 | 7.9 |
| **MoT** | **29.7** | 34.8 | **36.8** | **20.7** |

On **NL2Repo-Bench**, MoT reaches **29.7**, outperforming the strongest baseline by **4.3 points**.

#### RAL-Bench (GPT-5)

| Method | Functional Score |
| --- | ---: |
| Direct | 38.5 |
| Self-Reflection | 44.1 |
| SE-Agent | 44.7 |
| AlphaEvolve | 43.7 |
| CSE | 34.3 |
| **MoT** | **46.2** |

On **RAL-Bench**, MoT achieves the best score of **46.2**, exceeding the strongest baseline by **1.5 points**.

These results indicate that MoT transfers effectively from function-level generation to more realistic **repository-level natural-language-to-code generation**.

### 2. Comparison with Structured Reasoning Frameworks

We further compare MoT with representative structured reasoning methods on **RAL-Bench**, including Tree-of-Thoughts, Graph-of-Thoughts, Parsel, CodeChain, and CodeTree.

| Method (GPT-5) | RAL-Bench |
| --- | ---: |
| Direct | 38.5 |
| Tree-of-Thoughts | 43.3 |
| Graph-of-Thoughts | 45.1 |
| Parsel | 44.6 |
| CodeChain | 40.4 |
| CodeTree | 41.5 |
| **MoT** | **46.2** |

MoT achieves the best result in this comparison, suggesting that a **generation-aware hierarchical planning representation** is particularly effective for repository-level software engineering tasks.

### 3. Full LiveCodeBench Results

We also report additional results on the **full LiveCodeBench** for **GPT-4o-mini**.

| Method | Pass@1 |
| --- | ---: |
| Direct | 25.8 |
| CoT | 28.3 |
| SCoT | 37.5 |
| Self-Planning | 39.2 |
| **MoT** | **40.5** |

MoT achieves the best **Pass@1 = 40.5** among the compared prompting baselines on the full benchmark.


---

## Illustrative Example: Problem, Prompts, MLR Graph, and Generated Code

This section presents an end-to-end example showing how the **Multi-Level Reasoning (MLR) Graph** supports modular code generation.

We provide:

1. A **problem description**.
2. The **prompt templates** used to construct the MLR Graph and generate code.
3. A generated **MLR Graph**.
4. The final **modular code**.

### Prompt Template for MLR Graph

```python
You are a code reasoning assistant. Your task is to analyze the given programming problem and generate a modular reasoning graph (Multi-Level Reasoning Graph, MLR Graph) to guide the code generation process. Provide your reasoning in the following hierarchical textual format clearly:
### Format
H1 [High-Level]: Solve the problem: {Problem description}
  Reasoning: Break the problem into major tasks: {High-level task 1} and {High-level task 2}.
  ├── H1.1 [High-Level]: {Subtask 1 of High-Level}
  │       Reasoning: {Reasoning for subtask 1}
  │       ├── I1.1 [Intermediate-Level]: {Intermediate-level task 1 for subtask 1}
  │       │         Reasoning: {Reasoning for intermediate-level task 1}
  │       └── I1.2 [Intermediate-Level]: {Intermediate-level task 2 for subtask 1}
  │                 Reasoning: {Reasoning for intermediate-level task 2}
  ├── H1.2 [High-Level]: {Subtask 2 of High-Level}
  │       Reasoning: {Reasoning for subtask 2}
  │       ├── I2.1 [Intermediate-Level]: {Intermediate-level task 1 for subtask 2}
  │       │         Reasoning: {Reasoning for intermediate-level task 1}
  │       │         └── D2.1 [Detailed-Level]: {Detailed implementation details or pseudo-code}
```

### Prompt Template for Code Generation

```python
You are a code generation assistant. Your task is to generate modular code based on the given modular reasoning (MLR graph). You must only output the generated code.
Modular Reasoning (MLR graph): {MLR_graph}.
Output: Provide only the complete code corresponding to the given modular reasoning. If possible, organize the code into multiple modular functions.
```

### Visualization of the Prompting Process

![MLR Graph and Code Prompting](img/prompt.png)

### Problem Description

**Task:**
You are given a list of lists (an array of arrays) and an integer **K**. The goal is to **find the largest sum among the sublists** and then **divide this sum by K**.

### Generated MLR Graph

![MLR Graph](img/image.png)

### Generated Modular Code

```python
def validate_input(K):
    """D3.1.1: Check if K is zero"""
    if K == 0:
        raise ValueError("K cannot be zero")


def compute_sublist_sum(sublist):
    """D1.2.1: Compute sum using sum() function"""
    return sum(sublist)


def find_max_sublist_sum(array):
    """D2.1.1: Initialize max sum and find the maximum sublist sum"""
    max_sum = float('-inf')

    for sublist in array:
        sublist_sum = compute_sublist_sum(sublist)
        if sublist_sum > max_sum:
            max_sum = sublist_sum

    return max_sum


def divide_max_sum(max_sum, K):
    """D3.2.1: Perform division"""
    return max_sum / K


def largest_sum(array, K):
    """Main function that orchestrates modularized components"""
    validate_input(K)
    max_sum = find_max_sublist_sum(array)
    return divide_max_sum(max_sum, K)
```


