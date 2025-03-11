import json
import re


def read_jsonl(file_path):
    """ 读取 JSONL 文件 """
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            data.append(json.loads(line))
    return data


def extract_test_cases(test_code):
    """ 解析 test 代码，提取所有 assert 语句中的测试用例 """
    test_cases = []
    pattern = re.compile(r"assert\s+candidate\((.*?)\)\s*==\s*(True|False)", re.DOTALL)

    for match in pattern.finditer(test_code):
        args = match.group(1).strip()
        expected = match.group(2).strip() == "True"
        test_cases.append((args, expected))

    return test_cases


def run_test_cases(code, test_cases, function_name):
    """ 执行生成的代码并计算 APR """
    local_scope = {}
    passed = 0
    total = len(test_cases)

    try:
        # 自动补充常见的 import
        safe_code = "import math\nimport itertools\n" + code

        # 检查代码格式是否正确
        compile(safe_code, '<string>', 'exec')
        exec(safe_code, {}, local_scope)
        function = local_scope.get(function_name)

        if function is None:
            print(f"函数 {function_name} 未定义，所有测试用例判定为 False")
            return 0, 0, total, 'function_not_defined'

        for args, expected in test_cases:
            try:
                result = eval(f"function({args})", {}, {"function": function})
                if result == expected:
                    passed += 1
            except Exception as e:
                print(f"测试用例 {args} 失败，错误: {e}")
                return 0, 0, total, 'runtime_error'

    except SyntaxError as e:
        print(f"代码语法错误: {e}，所有测试用例判定为 False")
        return 0, 0, total, 'syntax_error'
    except Exception as e:
        print(f"代码执行失败: {e}，所有测试用例判定为 False")
        return 0, 0, total, 'execution_error'

    apr = passed / total if total > 0 else 0
    return apr, passed, total, 'success'


# 文件路径
file1_path = "data/dataset/HumanEval.jsonl"
file2_path = "data/results/HumanEval_deepseek/samples_CodeCoT_HumanEval_deepseek.jsonl"

# 读取 JSONL 文件
humaneval_data = read_jsonl(file1_path)
samples_data = read_jsonl(file2_path)

total_passed = 0
total_tests = 0
syntax_errors = 0
execution_errors = 0
function_not_defined_errors = 0
runtime_errors = 0
successful_runs = 0

for humaneval_item in humaneval_data:
    task_id = humaneval_item['task_id']
    test_code = humaneval_item['test']
    function_name = humaneval_item['entry_point']
    test_cases = extract_test_cases(test_code)

    # 查找匹配的样本代码
    generated_code = next((s['completion'] for s in samples_data if s['task_id'] == task_id), None)
    if generated_code:
        apr, passed_cases, total_cases, error_type = run_test_cases(generated_code, test_cases, function_name)
    else:
        print(f"任务 {task_id} 无法找到代码，所有测试用例判定为 False")
        passed_cases = 0
        total_cases = len(test_cases)
        error_type = 'code_not_found'

    total_passed += passed_cases
    total_tests += total_cases

    # 统计不同类型的失败
    if error_type == 'syntax_error':
        syntax_errors += 1
    elif error_type == 'execution_error':
        execution_errors += 1
    elif error_type == 'function_not_defined':
        function_not_defined_errors += 1
    elif error_type == 'runtime_error':
        runtime_errors += 1
    elif error_type == 'success':
        successful_runs += 1

# 计算整体 APR
overall_apr = total_passed / total_tests if total_tests > 0 else 0

print(f"整体 APR: {overall_apr}")
print(f"总通过的测试用例数: {total_passed}")
print(f"总测试用例数: {total_tests}")
print(f"成功执行的任务数: {successful_runs}")
print(f"代码语法错误任务数: {syntax_errors}")
print(f"执行时报错任务数: {execution_errors}")
print(f"函数未定义任务数: {function_not_defined_errors}")
print(f"运行时报错任务数: {runtime_errors}")