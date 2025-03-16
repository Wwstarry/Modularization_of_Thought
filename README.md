## Introduction
This repository contains the implementation of our paper:

**"[Modularization-of-Thought Prompting for Effective Code Generation]"**

Our research aims to address code generation by proposing MoT prompting technique. The key contributions include:
- **Contribution 1**: We propose a novel prompting technique, called MoT, to improve the code generation performance of LLMs by incorporating the modularization principles of software development into the reasoning process. 
- **Contribution 2**: We design a novel Multi-Level Reasoning Graph to further enhance modular understanding and ensure better alignment between reasoning steps and the generated code.
- **Contribution 3**:  We conducted extensive experiments on two LLMs (i.e., GPT-4o-mini and DeepSeek-R1) with six benchmarks, comparing them with eight baselines to demonstrate the effectiveness of MoT in improving code generation performance.

Prompts of MoT are presented in prompting techniques/MoT.py. 
  
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


## Project Structure

The following is the directory structure of our project:

📂 Modularization_of_Thought  
 ├── 📂 APR               # Contains Automated Program Repair (APR) scripts  
 │   ├── APR_HumanEval+.py   # APR method for HumanEval+ dataset  
 │   ├── APR_HumanEval.py    # APR method for HumanEval dataset  
 │   ├── APR_HumanEval_ET.py # APR method with extended testing for HumanEval  
 │   ├── APR_MBPP+.py        # APR method for MBPP+ dataset  
 │   ├── APR_MBPP.py         # APR method for MBPP dataset  
 │   ├── APR_MBPP_ET.py      # APR method with extended testing for MBPP  
 │  
 ├── 📂 Dataset            # Contains dataset files for experiments  
 │   ├── HumanEval+.jsonl      # HumanEval+ dataset  
 │   ├── HumanEval-ET.jsonl    # Extended version of HumanEval dataset  
 │   ├── HumanEval-ET.jsonl.gz # Compressed version of HumanEval-ET  
 │   ├── HumanEval.jsonl       # Standard HumanEval dataset  
 │   ├── MBPP-ET.jsonl.gz      # Compressed version of MBPP-ET dataset  
 │   ├── MBPP_ET.jsonl         # MBPP extended dataset  
 │   ├── MBPP_sanitized.jsonl  # Sanitized MBPP dataset  
 │   ├── MBPP_sanitized.jsonl.gz # Compressed sanitized MBPP dataset  
 │   ├── Mbpp+.jsonl           # MBPP+ dataset  
 │   ├── humaneval.jsonl       # Standard HumanEval dataset  
 │  
 ├── 📂 Pass@1             # Evaluation of model pass@1 metric  
 │   ├── 📂 evaluation       # Evaluation scripts and utilities  
 │   │   ├── __init__.py    # Module initialization  
 │   │   ├── data.py        # Data handling functions  
 │   │   ├── evaluate_functional_correctness.py # Evaluates functional correctness of generated code  
 │   │   ├── evaluation.py  # Main evaluation script  
 │   │   ├── execution.py   # Script for executing generated code  
 │   ├── requirements.txt   # Dependencies for evaluation  
 │   ├── setup.py           # Setup script for evaluation module  
 │  
 ├── 📂 experiments        # Experimental results and analysis  
 │   ├── 📂 RQ1            # Results for Research Question 1  
 │   │   ├── 📂 HumanEval_deepseek  # Results using DeepSeek model on HumanEval  
 │   │   ├── 📂 HumanEval_gpt-4o-mini  # Results using GPT-4o-mini on HumanEval  
 │   │   ├── 📂 MBPP_deepseek  # Results using DeepSeek model on MBPP  
 │   │   ├── 📂 MBPP_gpt-4o-mini  # Results using GPT-4o-mini on MBPP  
 │   ├── 📂 RQ2            # Results for Research Question 2  
 │  
 ├── 📂 prompting_techniques # Various prompting strategies used in the study  
 ├── 📂 tools              # Utility scripts and helper functions  
 │  
 ├── README.md            # Project documentation  


Here is the structured section for **Key Directories and Key Files**, incorporating the **prompting techniques** found in your dataset:

---

### **Key Directories**
- **`APR/`**: Contains Automated Program Repair (APR) scripts for different datasets.
- **`Dataset/`**: Includes datasets used for model training and evaluation.
- **`Pass@1/`**: Stores evaluation scripts and settings for measuring pass@1 performance.
  - `evaluation/`: Implements evaluation metrics and functional correctness checks.
- **`experiments/`**: Contains results and analysis for research questions (RQ1 & RQ2).
  - `RQ1/`: Experimental results for Research Question 1.
  - `RQ2/`: Experimental results for Research Question 2.
- **`prompting_techniques/`**: Stores different prompting techniques used in the experiments.
- **`tools/`**: Utility scripts and helper functions for data processing and experiment execution.

---

### **Key Files (Prompting Techniques)**
- **`Zero-shot prompting`** [Chen et al., 2021]: Generates code solely based on problem descriptions without examples.  
- **`Few-shot prompting`** [Chen et al., 2021]: Guides code generation by providing a few examples in the problem description.  
- **`CoT prompting`** [Wei et al., 2022]: Enhances code generation through step-by-step logical reasoning.  
- **`Self-planning prompting`** [Jiang et al., 2024]: Develops a structured plan before generating code to improve execution correctness.  
- **`SCoT prompting`** [Li et al., 2025]: Extends CoT prompting by integrating structured program components like loops and conditionals.  
- **`CodeCoT prompting`** [Huang et al., 2023]: Combines CoT reasoning with self-examination, where the model verifies generated code using test cases before refining outputs.

---

### Illustrative Example: Problem, Prompts, MLR Graph, and Generated Code

This section presents an **end-to-end example** demonstrating how the **Multi-Level Reasoning (MLR) Graph (MLR Graph)** facilitates modular code generation.  
We provide:
1. **Problem Description** – A programming task to be solved.
2. **Prompt Templates** – How we guide the LLM to generate the MLR Graph and corresponding code.
3. **MLR Graph** – A modular breakdown of the reasoning process.
4. **Generated Modular Code** – Python implementation based on the MLR Graph.



#### Prompt Template for MLR Graph and Code Generation

The first prompt directs the LLM to construct an **MLR Graph**, while the second instructs it to translate the modular reasoning into modular code.

**Visualization of the Prompting Process:**

![MLR Graph and Code Prompting](img/prompt.png)



####  Problem Description
**Task:**  
You are given a list of lists (an array of arrays) and an integer **K**.  
The goal is to **find the largest sum among the sublists** and then **divide this sum by K**.


####  MLR Graph: Modular Reasoning for Code Generation


**Generated MLR Graph:**
![MLR Graph](img/image.png)

---

## Generated Modular Code 

The modular MLR Graph leads to the following modular generated code:

```python
def validate_input(K):  
    """D3.1.1: Check if K is zero"""
    if K == 0:
        raise ValueError("K cannot be zero")  # D3.1.2: Raise error for zero division

def compute_sublist_sum(sublist):
    """D1.2.1: Compute sum using sum() function"""
    return sum(sublist)

def find_max_sublist_sum(array):
    """D2.1.1: Initialize max sum and find the maximum sublist sum"""
    max_sum = float('-inf')  # D2.1.1: Initialize max sum

    for sublist in array:  # D1.1.1: Iterate through the list of lists
        sublist_sum = compute_sublist_sum(sublist)  # Modularized sum computation
        if sublist_sum > max_sum:  # D2.1.2: Compare with current max
            max_sum = sublist_sum  # D2.1.3: Update max_sum
            
    return max_sum

def divide_max_sum(max_sum, K):
    """D3.2.1: Perform division"""
    return max_sum / K

def largest_sum(array, K):
    """Main function that orchestrates modularized components"""
    validate_input(K)  # Validate K before proceeding
    max_sum = find_max_sublist_sum(array)  # Compute max sublist sum
    return divide_max_sum(max_sum, K)  # Compute final result
```

