import json
from human_eval.data import read_problems, write_jsonl
import openai
from openai import OpenAI
import httpx
import ell
import traceback
import re
from typing import List, Tuple, Optional,Dict, Any

#Client

@ell.simple(model="deepseek-r1", client=client)
def MoT(problem: str):
    """
You are a Mo-of-Thought Generation Agent. Your task is to analyze the problem and generate an expected Multi-Level Reasoning Graph for code generation. You must only output the graph.

###  Format

H1 [High-Level]: Solve the problem: {Problem description}
  Reasoning: Break the problem into major tasks: {High-level task 1}, {High-level task 2}, and {High-level task 3}.
  ├── H1.1 [High-Level]: {Subtask 1 of High-Level}
  │       Reasoning: {Reasoning for subtask 1}
  │       ├── I1.1 [Intermediate-Level]: {Intermediate-level task 1 for subtask 1}
  │       │         Reasoning: {Reasoning for intermediate-level task 1}
  │       └── I1.2 [Intermediate-Level]: {Intermediate-level task 2 for subtask 1}
  │                 Reasoning: {Reasoning for intermediate-level task 2}
  ├── H1.2 [High-Level]: {Subtask 2 of Top-Level}
  │       Reasoning: {Reasoning for subtask 2}
  │       ├── I2.1 [Intermediate-Level]: {Intermediate-level task 1 for subtask 2}
  │       │         Reasoning: {Reasoning for intermediate-level task 1}
  │       │         └── D2.1 [Detailed-Level]: {Code snippet for detailed-level task 1}
  │       └── I2.2 [Intermediate-Level]: {Intermediate-level task 2 for subtask 2}
  │                 Reasoning: {Reasoning for intermediate-level task 2}
  │                 └── D2.2 [Detailed-Level]: {Code snippet for detailed-level task 2}
  └── H1.3 [High-Level]: {Subtask 3 of Top-Level}
          Reasoning: {Reasoning for subtask 3}
          └── I3.1 [Intermediate-Level]: {Intermediate-level task for subtask 3}
                    Reasoning: {Reasoning for intermediate-level task}
                    └── D3.1 [Detailed-Level]: {Code snippet for detailed-level task}
                    
    """
    return (
        f"Here is the problem:\n{problem}\n"
    )

@ell.simple(model="deepseek-r1", client=client)
def Code(problem: str, graph: str):
    """
    You are a Code Generation Agent. Your task is to generate a expected code. You Must only output the generated code.
    """ 
    return (
        f"Here is the analyse of the problem: \n{graph}\n"
        f"Here is the problem:\n{problem}\nYou Must only output the generated code."
    )


def extract_code(text: str) -> str:
    """
    Extract code from a text block using regular expressions.

    Args:
        text (str): The input text containing code.

    Returns:
        str: The extracted code block.
    """
    # Regex pattern to match Python code block
    code_pattern = r"```python(.*?)```"  # Matches code within ```python and ```
    match = re.search(code_pattern, text, re.DOTALL)  # Allow multiline matches
    if match:
        return match.group(1).strip()  # Extract code content without markers
    return text.strip()  # Return original if no match is found

def append_to_jsonl(file_path: str, data: Dict[str, Any]):
    """
    Append a single record to a JSONL file.

    Args:
        file_path (str): The path to the JSONL file.
        data (Dict[str, Any]): The data to append.
    """
    with open(file_path, "a") as f:
        f.write(json.dumps(data) + "\n")



# Read HumanEval problems
problems = read_problems()
print("read_problems is done!")

output_file = "samples_MoT_deepseek_cost.jsonl"

for task_id in list(problems)[:10]:
    try:
        problem_info = problems[task_id]
        print(task_id)

        problem = problem_info["prompt"]
        # Call the Code function (you need to implement it or provide it)
        graph = MoT(problem)
        print(graph)
        IR_graph = extract_code(graph)

        code = Code(problem, IR_graph)
        code = extract_code(code)
        # print(code)

        # Append the generated result to JSONL file
        append_to_jsonl(output_file, {
            "task_id": task_id,
            "completion": code
        })

    except Exception as e:
        print(f"Error processing task {task_id}: {e}")
        traceback.print_exc()
