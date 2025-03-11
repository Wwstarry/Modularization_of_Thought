import json
from human_eval.data import write_jsonl, read_problems
import openai
from openai import OpenAI
import re
import httpx
import traceback
from typing import List, Tuple, Optional,Dict, Any

# client

agent = "You are a code developer assistant. Return the function code only."

text = """Please return Chain of Thought Reasoning, Response and Testing the Function according to Input only.Please follow this example:
### Input:
def factorial(n):
    \"\"\"
    Return the factorial of n.
    >>> factorial(2)
    2
    >>> factorial(0)
    1
    \"\"\"

###Chain of thought:
First, we recognize that the factorial of a number is the product of all positive integers from 1 to that number.
There are two common approaches to calculating the factorial: iteratively and recursively.
For this task, we'll go with the iterative approach as it's straightforward and avoids potential issues with recursion limits for larger numbers.
The iterative approach involves initializing a variable to 1 and then multiplying it with every integer from 1 to n.
We also need to handle the edge case where n is 0, since 0! (0 factorial) is defined as 1.
Finally, we'll test the function to ensure it works correctly.

### Testing the Function:
```python
assert factorial(0)==1 # factorial(0) should return 1
assert factorial(0)==1 # factorial(1) should return 1
assert factorial(2)==2 # factorial(2) should return 2
assert factorial(5)==120 # factorial(5) should return 120
assert factorial(10)==3628800 # factorial(10) should return 3628800
```

### Response:
```python
def factorial(n):
    \"\"\"
    >>> factorial(9)
    362880
    >>> factorial(0)
    1
    \"\"\"
    if n == 0:
        return 1
    result = 1
    for i in range(1, n+1):
        result *= i
    return result
```
"""


def generate_one_completion(prompt):
    prompt = prompt+"\n"+text
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model="deepseek-r1",
    )

    # print(chat_completion)
    return chat_completion.choices.pop().message.content

def extract_code_and_tests(text: str):

    code_pattern = r"### Response:\n```python\n(.*?)```"
    test_pattern = r"### Testing the Function:\n```python\n(.*?)```"

    code_match = re.search(code_pattern, text, re.DOTALL)
    code = code_match.group(1).strip() if code_match else ""

    test_match = re.search(test_pattern, text, re.DOTALL)
    test_text = test_match.group(1).strip() if test_match else ""
    return code, test_text

problems = read_problems()

print("read_problems is done!")

samples = []

def write_jsonl(file_path, data):

    with open(file_path, 'a', encoding='utf-8') as f:

        for item in data:
            f.write(json.dumps(item) + '\n')

def generate_code_from_feedback(feedback):
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": feedback,
            }
        ],
        model="deepseek-r1",
    )

    return chat_completion.choices.pop().message.content

def test_code(code: str, test_cases: str) -> List[str]:
    failed_tests = []
    namespace = {'List': List}  # 添加额外的类型支持，如果需要
    try:
        exec(code, namespace)  # 使用隔离的命名空间执行代码
        for test_case in test_cases.split("\n"):
            if test_case.strip().startswith("assert"):
                try:
                    exec(test_case, namespace)
                except AssertionError as e:
                    failed_tests.append(f"Test Failed: {test_case}, AssertionError: {str(e)}")
                except Exception as e:
                    failed_tests.append(f"Test Failed: {test_case}, Error: {str(e)}")
    except Exception as e:
        failed_tests.append(f"Code Execution Error, Error: {traceback.format_exc()}")

    return failed_tests

def extract_code_if_present(text: str) -> str:
    match = re.search(r"```python\n([\s\S]*?)\n```", text)
    

    return match.group(1) if match else text

for task_id in list(problems)[:]:
    problem_info = problems[task_id]
    print(task_id)
    prompt = problem_info["prompt"] + "\n"+ problem_info["test"]
    cot = generate_one_completion(prompt)
    # print(cot)
    code, test_cases = extract_code_and_tests(cot)
    feedback = code

    n=0

    while True:

        failed_tests = test_code(code, test_cases)

        if n>2:
            break

        if not failed_tests:

            break

        feedback += "\nFailed tests:\n" + "\n".join(failed_tests)
        # print(feedback)

        prompt_feedback = code + '\n' + feedback + '\n' + agent
        new_code = generate_code_from_feedback(prompt_feedback)

        code = new_code
        # print(code)
        n+=1
        print(n)
    final_code = extract_code_if_present(code)
    print(final_code)
    samples.append({"task_id": task_id, "completion": final_code})

    write_jsonl("samples_CodeCoT_deepseek_cost.jsonl", samples)
    samples = []