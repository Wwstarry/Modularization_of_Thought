import json
from human_eval.data import write_jsonl, read_problems
import openai
from openai import OpenAI
import re
import httpx
import traceback
from typing import List, Tuple, Optional,Dict, Any

# client

# example = """
# ### Output Format:
# ```python
# def function_name(args):
#     '''
#     <Problem Description>
#     Step-by-Step Plan:
#     1. <Step 1 description>
#     2. <Step 2 description>
#     3. <Step 3 description>
#     '''
#     <Implementation based on the plan>

# Here is an output example:
# ```python
# def minSubArraySum(nums):
#     '''
#     Given an array of integers nums, find the minimum sum of any
#     non-empty sub-array of nums.

#     Example:
#     minSubArraySum([2, 3, 4, 1, 2, 4]) == 1
#     minSubArraySum([-1, -2, -3]) == -6

#     Step-by-Step Plan:
#     1. Create a function to calculate the sum of a sub-array.
#     2. Loop through the input list, calculating the sum of each sub-array.
#     3. Update and return the minimum sum.
#     '''

#     # Helper function to calculate the sum of a sub-array
#     def subArraySum(nums):
#         sum = 0
#         for i in nums:
#             sum += i
#         return sum

#     # Implementation starts here
#     min_sum = subArraySum(nums)  # Initialize with full array sum
#     for i in range(len(nums)):
#         for j in range(i + 1, len(nums) + 1):
#             current_sum = subArraySum(nums[i:j])
#             if current_sum < min_sum:
#                 min_sum = current_sum
#     return min_sum
# ```
# """

example = """
Here is an output example:
```python
def minSubArraySum(nums):
    '''
    Given an array of integers nums, find the minimum sum of any
    non-empty sub-array of nums.

    Example:
    minSubArraySum([2, 3, 4, 1, 2, 4]) == 1
    minSubArraySum([-1, -2, -3]) == -6

    Step-by-Step Plan:
    1. Create a function to calculate the sum of a sub-array.
    2. Loop through the input list, calculating the sum of each sub-array.
    3. Update and return the minimum sum.
    '''

    # Helper function to calculate the sum of a sub-array
    def subArraySum(nums):
        sum = 0
        for i in nums:
            sum += i
        return sum

    # Implementation starts here
    min_sum = subArraySum(nums)  # Initialize with full array sum
    for i in range(len(nums)):
        for j in range(i + 1, len(nums) + 1):
            current_sum = subArraySum(nums[i:j])
            if current_sum < min_sum:
                min_sum = current_sum
    return min_sum
```
"""


text = "Here is the problem. Please only provide the final output(Step-by-Step Plan should be brief and not beyond 150 words).\n"





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
        # model="gpt-3.5-turbo",
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
    # write_jsonl("samples_Self-planning_HumanEval_deepseek.jsonl", samples)
    write_jsonl("samples_Self-planning_HumanEval_gpt-4o-mini.jsonl", samples)
    samples = []

