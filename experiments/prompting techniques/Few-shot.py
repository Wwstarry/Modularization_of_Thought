import json
from human_eval.data import write_jsonl, read_problems
import openai
from openai import OpenAI
import re
import httpx
import traceback
from typing import List, Tuple, Optional,Dict, Any

# client



example = """
Here are some examples:
### Problem
from typing import List\n\n\ndef has_close_elements(numbers: List[float], threshold: float) -> bool:\n    \"\"\" Check if in given list of numbers, are any two numbers closer to each other than\n    given threshold.\n    >>> has_close_elements([1.0, 2.0, 3.0], 0.5)\n    False\n    >>> has_close_elements([1.0, 2.8, 3.0, 4.0, 5.0, 2.0], 0.3)\n    True\n    \"\"\"\n
### Output
```python
    for idx, elem in enumerate(numbers):\n        for idx2, elem2 in enumerate(numbers):\n            if idx != idx2:\n                distance = abs(elem - elem2)\n                if distance < threshold:\n                    return True\n\n    return False\n
```

### Problem
from typing import List\n\n\ndef separate_paren_groups(paren_string: str) -> List[str]:\n    \"\"\" Input to this function is a string containing multiple groups of nested parentheses. Your goal is to\n    separate those group into separate strings and return the list of those.\n    Separate groups are balanced (each open brace is properly closed) and not nested within each other\n    Ignore any spaces in the input string.\n    >>> separate_paren_groups('( ) (( )) (( )( ))')\n    ['()', '(())', '(()())']\n    \"\"\"\n
### Output
```python
    result = []\n    current_string = []\n    current_depth = 0\n\n    for c in paren_string:\n        if c == '(':\n            current_depth += 1\n            current_string.append(c)\n        elif c == ')':\n            current_depth -= 1\n            current_string.append(c)\n\n            if current_depth == 0:\n                result.append(''.join(current_string))\n                current_string.clear()\n\n    return result\n
```
"""

text = "Here is the problem. Please only provide the final code.\n"


def generate_one_completion(prompt):
    prompt = example+text+prompt
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

for task_id in list(problems)[:]: 
    problem_info = problems[task_id]
    print(task_id)
    prompt = problem_info["prompt"]
    code = generate_one_completion(prompt)
    # print(code)
    final_code = extract_code_if_present(code)
    # print(final_code)
    samples.append({"task_id": task_id, "completion": final_code})
    write_jsonl("samples_Few_shot_HumanEval_gpt-4o-mini.jsonl", samples)
    samples = []