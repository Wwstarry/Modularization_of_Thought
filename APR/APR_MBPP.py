import json
import tempfile
import importlib.util
import sys
import pandas as pd

# 文件路径
mbpp_file_path = "data/dataset/Mbpp-ET.jsonl"
code_file_path = "data/results/MBPP_gpt-4o-mini/samples_CodeCoT_MBPP_gpt-4o-mini.jsonl"

# 读取并解析 JSONL 文件内容
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
mbpp_data = load_jsonl(mbpp_file_path)
code_data = load_jsonl(code_file_path)

# 生成任务 ID 到测试用例和 entry_point（函数名）的映射
test_cases_map = {}
entry_point_map = {}  # 存储函数名
for entry in mbpp_data:
    task_id = entry.get("task_id")
    if task_id and "test" in entry and "entry_point" in entry:
        test_cases_map[task_id] = entry["test"]
        entry_point_map[task_id] = entry["entry_point"]  # 直接获取 entry_point

# 生成任务 ID 到代码实现的映射
code_map = {}
for entry in code_data:
    task_id = entry.get("task_id")
    completion = entry.get("completion")
    if task_id and completion:
        # 统一任务 ID 格式（去除大小写差异）
        normalized_task_id = task_id.replace("MBPP", "Mbpp")
        code_map[normalized_task_id] = completion

# 找出没有代码实现的任务
unmatched_tasks = [task_id for task_id in test_cases_map if task_id not in code_map]
if unmatched_tasks:
    print(f"未找到代码的任务: {unmatched_tasks}")

# 计算 APR
apr_results = {}
total_passed = 0
total_tests = 0
error_log = {}  # 存储执行失败的任务及错误信息

for task_id, test_code in test_cases_map.items():
    test_count = len(test_code.split("\n")) - 1  # 计算测试用例总数
    total_tests += test_count  # 更新总测试用例数

    if task_id in code_map:
        code = code_map[task_id]
        entry_point = entry_point_map[task_id]  # 直接获取函数名

        # 生成完整 Python 代码
        full_code = f"{code}\n\n{test_code}\ncheck({entry_point})"

        # 在临时 Python 文件中运行代码
        with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as temp_file:
            temp_filename = temp_file.name
            temp_file.write(full_code.encode())

        # 动态导入模块
        spec = importlib.util.spec_from_file_location("module_name", temp_filename)
        module = importlib.util.module_from_spec(spec)
        sys.modules["module_name"] = module

        try:
            spec.loader.exec_module(module)
            passed_tests = test_count  # 如果代码执行成功，则所有测试通过
        except Exception as e:
            print(f"任务 {task_id} 代码执行失败: {e}")
            error_log[task_id] = str(e)  # 记录错误信息
            passed_tests = 0  # 代码执行失败，所有测试未通过

    else:
        # 没有找到代码的任务，所有测试用例都视为失败
        passed_tests = 0

    total_passed += passed_tests  # 更新总通过的测试数
    apr = passed_tests / test_count if test_count > 0 else 0
    apr_results[task_id] = apr  # 记录每个任务的 APR

# 计算整体 APR
overall_apr = total_passed / total_tests if total_tests > 0 else 0

# 输出结果
print(f"整体 APR: {overall_apr}")
print(f"总通过的测试用例数: {total_passed}")
print(f"总测试用例数: {total_tests}")

# 显示 APR 结果
apr_df = pd.DataFrame(list(apr_results.items()), columns=["Task ID", "APR"])
print(apr_df)

# 记录错误日志到文件
if error_log:
    with open("error_log.json", "w", encoding="utf-8") as f:
        json.dump(error_log, f, indent=4, ensure_ascii=False)
    print("\n===== 代码执行错误日志已保存至 error_log.json =====")
