import json
import re
import sys
import ast
import platform
import threading


# 读取 JSONL 文件
def read_jsonl_as_dict(file_path, key_field):
    data_dict = {}
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            record = json.loads(line.strip())
            key = record[key_field].lower()
            data_dict[key] = record
    return data_dict


def rename_function(code, old_name, new_name):
    pattern = rf"\b{re.escape(old_name)}\b"
    return re.sub(pattern, new_name, code)


def extract_function_name(code):
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                return node.name
    except Exception:
        pass
    return None


def normalize_text(text):
    full_to_half = {
        '，': ',', '。': '.', '？': '?', '！': '!', '：': ':', '；': ';', '、': ','
    }
    for full, half in full_to_half.items():
        text = text.replace(full, half)
    return text


def run_with_timeout(code, local_env, timeout=5):
    """ 运行代码并设置超时时间 """

    def exec_code():
        try:
            exec(code, local_env)
        except Exception as e:
            local_env["error"] = f"代码执行失败: {e}"

    thread = threading.Thread(target=exec_code)
    thread.start()
    thread.join(timeout)

    if thread.is_alive():
        return "超时"
    return local_env.get("error", "成功")


def compute_apr(mbpp_data, model_data):
    total_tests = 0
    passed_tests = 0
    failed_tasks = []

    sys.setrecursionlimit(1000)

    for task_id, mbpp_entry in mbpp_data.items():
        if task_id not in model_data:
            continue

        code = model_data[task_id]["completion"]
        test_code = mbpp_entry.get("test", "")
        entry_point = mbpp_entry.get("entry_point")
        if not test_code or not entry_point:
            continue

        code = normalize_text(code)
        test_code = normalize_text(test_code)

        detected_func = extract_function_name(code)
        if detected_func and detected_func != "generated_function":
            code = rename_function(code, detected_func, "generated_function")

        test_code = rename_function(test_code, entry_point, "generated_function")
        code = rename_function(code, entry_point, "generated_function")

        prelude = "from collections import Counter\nimport math\nimport itertools"
        local_env = {}
        exec(prelude, local_env)

        result = run_with_timeout(code, local_env)
        if result == "超时":
            failed_tasks.append((task_id, "代码执行超时"))
            continue
        elif result.startswith("代码执行失败"):
            failed_tasks.append((task_id, result))
            continue

        if "generated_function" not in local_env:
            exec("def generated_function(*args, **kwargs): pass", local_env)
            failed_tasks.append((task_id, f"未找到函数: {entry_point}"))
            continue

        try:
            exec(test_code, local_env)
            test_func = local_env["check"]
            test_func(local_env["generated_function"])
            passed_tests += test_code.count("assert")
        except AssertionError:
            failed_tasks.append((task_id, "部分测试未通过"))
        except RecursionError:
            failed_tasks.append((task_id, "递归深度超限"))
        except TypeError as e:
            failed_tasks.append((task_id, f"类型错误: {e}"))
        except Exception as e:
            failed_tasks.append((task_id, f"测试代码执行失败: {e}"))

        total_tests += test_code.count("assert")

    overall_apr = passed_tests / total_tests if total_tests > 0 else 0
    return overall_apr, passed_tests, total_tests, failed_tasks


# 读取数据
mbpp_data = read_jsonl_as_dict("data/dataset/MBPP-ET.jsonl", "task_id")
deepseek_data = read_jsonl_as_dict("data/results/MBPP_gpt-4o-mini/samples_Few_shot_MBPP_gpt-4o-mini.jsonl", "task_id")


overall_apr, total_passed, total_tests, error_logs = compute_apr(mbpp_data, deepseek_data)

print(f"整体 APR: {overall_apr}")
print(f"总通过的测试用例数: {total_passed}")
print(f"总测试用例数: {total_tests}")
print("错误日志:", error_logs[:10])
