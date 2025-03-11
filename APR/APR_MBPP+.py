import json
import re


def parse_mbpp(file_path):
    """ 解析 Mbpp+.jsonl 提取测试用例 """
    mbpp_tests = {}
    with open(file_path, "r", encoding="utf-8") as file:
        for line in file:
            data = json.loads(line.strip())
            task_id = data["task_id"].replace("Mbpp/", "MBPP/")  # 统一 task_id 格式
            function_name = data["entry_point"]
            test_cases = data["assertion"].split("\n")
            test_cases = [tc.strip() for tc in test_cases if tc.startswith("assert ")]
            mbpp_tests[task_id] = {"function_name": function_name, "test_cases": test_cases}
    return mbpp_tests


def parse_code(file_path):
    """ 解析 samples_CodeCoT_MBPP_deepseek.jsonl 提取代码实现 """
    code_snippets = {}
    with open(file_path, "r", encoding="utf-8") as file:
        for line in file:
            data = json.loads(line.strip())
            task_id = data["task_id"]
            code_snippets[task_id] = data["completion"]
    return code_snippets


def evaluate_mbpp_code(code_snippets, test_cases):
    """ 运行代码并计算 APR """
    total_tests = 0
    passed_tests = 0
    failed_cases = []
    task_failures = {}

    for task_id, code in code_snippets.items():
        if task_id in test_cases:
            function_name = test_cases[task_id]["function_name"]
            test_code_list = test_cases[task_id]["test_cases"]

            # 替换函数名，确保 `exec()` 能运行
            modified_code = re.sub(r"def (\w+)\(", f"def {function_name}(", code)

            try:
                namespace = {}
                exec(modified_code, namespace)

                for test in test_code_list:
                    total_tests += 1
                    try:
                        exec(test, namespace)
                        passed_tests += 1
                    except Exception as e:
                        failed_cases.append((task_id, test, str(e)))
                        task_failures[task_id] = task_failures.get(task_id, 0) + 1

            except Exception as e:
                for test in test_code_list:
                    total_tests += 1
                    failed_cases.append((task_id, test, f"Execution failure: {str(e)}"))
                    task_failures[task_id] = task_failures.get(task_id, 0) + 1

    apr = passed_tests / total_tests if total_tests > 0 else 0
    sorted_failures = sorted(task_failures.items(), key=lambda x: x[1], reverse=True)
    return apr, total_tests, passed_tests, failed_cases, sorted_failures


# 文件路径
mbpp_file_path = "data/dataset/Mbpp+.jsonl"
deepseek_file_path = "data/results/MBPP_deepseek/samples_CoT_MBPP_deepseek.jsonl"

# 读取数据
mbpp_tests = parse_mbpp(mbpp_file_path)
code_snippets = parse_code(deepseek_file_path)

# 计算 APR
apr_mbpp, total_tests_mbpp, passed_tests_mbpp, failed_tests_mbpp, top_failed_tasks_mbpp = evaluate_mbpp_code(
    code_snippets, mbpp_tests)

# 输出最终 APR 及相关统计数据
print(f"APR: {apr_mbpp}")
print(f"总测试用例数: {total_tests_mbpp}")
print(f"通过的测试用例数: {passed_tests_mbpp}")
print("失败最多的任务:", top_failed_tasks_mbpp[:5])
