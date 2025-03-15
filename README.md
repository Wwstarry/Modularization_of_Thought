## Introduction
This repository contains the implementation of our paper:

**"[Modularization-of-Thought Prompting for Effective Code Generation]"**


Our research aims to address code generation by proposing MoT prompting technique. The key contributions include:
- **Contribution 1**: We propose a novel prompting technique, called MoT, to improve the code generation performance of LLMs by incorporating the modularization principles of software development into the reasoning process. To further enhance modular understanding and reduce the discrepancy between initial reasoning and final output, we design a novel Multi-Level Reasoning Graph.
- **Contribution 2**: We conducted extensive experiments on two LLMs (i.e., GPT-4o-mini and DeepSeek-R1) with six benchmarks, comparing them with eight baselines to demonstrate the effectiveness of MoT in improving code generation performance. To encourage future research in this area and facilitate replication, we have made our data and code publicly available at https://anonymous.4open.science/r/Modularization-of-thought

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

### Detailed Version of the Example MLR Graph

![描述文本](img/image.png)




