import json
from human_eval.data import write_jsonl, read_problems
import openai
from openai import OpenAI
import re
import httpx
import traceback
from typing import List, Tuple, Optional,Dict, Any

# client




text = "Please solve the problem step by step. Please provide the chain of thought briefly and give the final code.\n"


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

for task_id in list(problems)[:10]: 
    problem_info = problems[task_id]
    print(task_id)
    prompt = problem_info["prompt"]
    code = generate_one_completion(prompt)
    # print(code)
    final_code = extract_code_if_present(code)
    # print(final_code)
    samples.append({"task_id": task_id, "completion": final_code})
    write_jsonl("samples_CoT_HumanEval_gpt-4o-mini.jsonl", samples)
    samples = []