import json
from human_eval.data import write_jsonl, read_problems
import openai
from openai import OpenAI
import re
import httpx
import traceback
from typing import List, Tuple, Optional,Dict, Any

# client





text ="""
Here is an example：
Please understand the requirement and write a rough solvingprocess. It starts with a input-output structure. You should use three basic structures to build the solving process, including sequences, branches, and loops. The necessary details should be written in natural languages.

### Problem
Write a python function to find the first repeated 
character in a given string.

### SCoT
Input: str: a string
Output: ch: a repeated character in str
1: for each character ch in str:
2: if ch appears more than once in str:
3: return ch
4: return None

Please understand the requirement and write a rough solvingprocess. It starts with a input-output structure. You should use three basic structures to build the solving process, including sequences, branches, and loops. The necessary details should be written in natural languages.
Here is the problem, Please only provide its SCoT and the final code(SCoT should be briefly and not beyond 200 words):
"""
def generate_one_completion(prompt):
    prompt = text+prompt
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model="gpt-4o-mini",
        # model="gpt-4o-mini",
    )

    # print(chat_completion)
    return chat_completion.choices.pop().message.content


problems = read_problems()

print("read_problems is done!")

samples = []

def write_jsonl(file_path, data):

    with open(file_path, 'a', encoding='utf-8') as f:

        for item in data:
            f.write(json.dumps(item) + '\n')


def extract_code_if_present(text: str) -> str:
    match = re.search(r"```python\n([\s\S]*?)\n```", text)

    return match.group(1) if match else text

for task_id in list(problems)[:]: 
    problem_info = problems[task_id]
    print(task_id)
    prompt = problem_info["prompt"]
    code = generate_one_completion(prompt)
    # print(code)
    final_code = extract_code_if_present(code)
    # print(final_code)
    samples.append({"task_id": task_id, "completion": final_code})
    # write_jsonl("samples_SCoT_HumanEval_deepseek.jsonl", samples)
    write_jsonl("samples_SCoT_HumanEval_gpt-4o-mini.jsonl", samples)
    samples = []