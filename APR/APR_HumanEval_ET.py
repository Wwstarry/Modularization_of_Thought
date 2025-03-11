import json
import tempfile
import importlib.util
import sys
import pandas as pd
import os

# 确保目录存在
output_dir = "E:/user/Desktop/apr"
os.makedirs(output_dir, exist_ok=True)

# 文件路径
test_file_path = "data/dataset/HumanEval-ET.jsonl"
code_file_path = "data/results/HumanEval_gpt-4o-mini/samples_Zero_shot_HumanEval_gpt-4o-mini.jsonl"
output_csv_path = f"{output_dir}/apr_results.csv"
error_log_path = f"{output_dir}/error_log.json"

# 读取 JSONL 文件
def load_jsonl(file_path):
    data = []
    with open(file_path, "r", encoding="utf-8") as file:
        for line in file:
            try:
                data.append(json.loads(line.strip()))
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")
    return data

# 加载数据
test_data = load_jsonl(test_file_path)
code_data = load_jsonl(code_file_path)

# 生成 task_id 到测试用例和函数名的映射
test_cases_map = {}
entry_point_map = {}
for entry in test_data:
    task_id = entry.get("task_id")
    if task_id and "test" in entry and "entry_point" in entry:
        test_cases_map[task_id] = entry["test"]
        entry_point_map[task_id] = entry["entry_point"]

# 生成 task_id 到代码实现的映射
code_map = {}
for entry in code_data:
    task_id = entry.get("task_id")
    completion = entry.get("completion")
    if task_id and completion:
        code_map[task_id] = completion

# 记录未找到代码的任务
unmatched_tasks = [task_id for task_id in test_cases_map if task_id not in code_map]
if unmatched_tasks:
    print(f"未找到代码的任务: {unmatched_tasks}")

# 计算 APR
apr_results = {}
total_passed = 0
total_tests = 0
error_log = {}

# 运行测试并计算 APR
for task_id, test_code in test_cases_map.items():
    test_count = len(test_code.split("\n")) - 1  # 计算测试用例总数
    total_tests += test_count  # 更新总测试用例数
    passed_tests = 0  # 默认所有测试未通过

    if task_id in code_map:
        code = code_map[task_id]
        entry_point = entry_point_map[task_id]

        # 组合完整的 Python 代码
        full_code = f"{code}\n\n{test_code}\ncheck({entry_point})"

        # 创建临时 Python 文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as temp_file:
            temp_filename = temp_file.name
            temp_file.write(full_code.encode())

        # 动态导入模块
        spec = importlib.util.spec_from_file_location("module_name", temp_filename)
        module = importlib.util.module_from_spec(spec)
        sys.modules["module_name"] = module

        try:
            spec.loader.exec_module(module)
            passed_tests = test_count  # 代码执行成功，所有测试通过
        except Exception as e:
            print(f"任务 {task_id} 代码执行失败: {e}")
            error_log[task_id] = str(e)
            passed_tests = 0

    else:
        error_log[task_id] = "代码缺失"

    total_passed += passed_tests  # 更新通过的测试数
    apr = passed_tests / test_count if test_count > 0 else 0
    apr_results[task_id] = apr  # 记录每个任务的 APR

# 计算整体 APR
overall_apr = total_passed / total_tests if total_tests > 0 else 0

# 输出结果
print(f"整体 APR: {overall_apr}")
print(f"总通过的测试用例数: {total_passed}")
print(f"总测试用例数: {total_tests}")

# 记录 APR 结果
apr_df = pd.DataFrame(list(apr_results.items()), columns=["Task ID", "APR"])
apr_df.to_csv(output_csv_path, index=False)
print(f"APR 结果已保存至 {output_csv_path}")

# 记录错误日志
if error_log:
    with open(error_log_path, "w", encoding="utf-8") as f:
        json.dump(error_log, f, indent=4, ensure_ascii=False)
    print(f"\n===== 代码执行错误日志已保存至 {error_log_path} =====")
