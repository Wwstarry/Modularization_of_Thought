import json
import traceback


def load_jsonl(file_path):
    """ 读取 JSONL 文件 """
    data = []
    with open(file_path, "r", encoding="utf-8") as file:
        for line in file:
            data.append(json.loads(line.strip()))
    return data


def fix_function_name(code, new_name="candidate"):
    """ 替换代码中的函数名，使其匹配测试用例所需的 candidate """
    import re
    pattern = r"def (\w+)\("
    match = re.search(pattern, code)
    if match:
        old_name = match.group(1)
        return code.replace(f"def {old_name}(", f"def {new_name}(")
    return code  # 如果找不到函数定义，返回原代码


def is_valid_python_code(code):
    """ 检查代码是否是有效的 Python 代码 """
    return "def " in code  # 确保代码至少有一个函数定义


def is_complete_python_code(code):
    """ 检查代码是否完整 """
    lines = code.strip().split("\n")
    return len(lines) > 2 and "def " in code


def evaluate_code(code_snippets, test_cases):
    """ 运行代码并计算 APR """
    total_tests = 0
    passed_tests = 0
    failed_cases = []
    task_failures = {}

    for task_id, code in code_snippets.items():
        if task_id in test_cases and is_complete_python_code(code):
            test_code_list = test_cases[task_id]
            try:
                namespace = {}
                fixed_code = fix_function_name(code)
                exec(fixed_code, namespace)

                if "candidate" not in namespace:
                    continue

                for test in test_code_list:
                    total_tests += 1
                    try:
                        exec(test, namespace)
                        passed_tests += 1
                    except Exception as e:
                        failed_cases.append((task_id, test, str(e)))
                        task_failures[task_id] = task_failures.get(task_id, 0) + 1
            except Exception as e:
                print(f"Execution error in {task_id}: {traceback.format_exc()}")

    apr = passed_tests / total_tests if total_tests > 0 else 0
    sorted_failures = sorted(task_failures.items(), key=lambda x: x[1], reverse=True)
    return apr, passed_tests, total_tests, failed_cases, sorted_failures


# 示例：加载数据并计算 APR
file1_path = "data/dataset/HumanEval+.jsonl"
file2_path = "data/results/HumanEval_deepseek/samples_Few_shot_HumanEval_deepseek.jsonl"

test_cases = {entry["task_id"]: entry["test"] for entry in load_jsonl(file1_path)}
code_snippets = {entry["task_id"]: entry["completion"] for entry in load_jsonl(file2_path)}

overall_apr, total_passed, total_tests, failed_tests, top_failed_tasks = evaluate_code(code_snippets, test_cases)

print(f"整体 APR: {overall_apr}")
print(f"总通过的测试用例数: {total_passed}")
print(f"总测试用例数: {total_tests}")
print("Top Failed Tasks:", top_failed_tasks[:5])
