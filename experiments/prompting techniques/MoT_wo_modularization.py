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
    You are a Reasoning Generation Agent. Your task is to analyze the problem 
    and generate a monolithic analysis for code generation. You Must only output the anaylsis (should not more than 100 words), which should not be modular.

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

output_file = "samples_MoT_wo_modularization_MBPP_deepseek.jsonl"

for task_id in list(problems)[:]:
    try:
        problem_info = problems[task_id]
        print(task_id)

        problem = problem_info["prompt"]
        # Call the Code function (you need to implement it or provide it)
        graph = MoT(problem)
        print(graph)
        IR_graph = extract_code(graph)
        # print(IR_graph)
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
