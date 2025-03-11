import re

def extract_and_save_code(input_file, output_file):
    # 正则表达式：匹配 completion 字段中的代码部分（从 def 开始）
    code_pattern = r'("completion":\s*")[\s\S]*?(def\s[\s\S]*?)"'

    # 打开原文件读取内容
    with open(input_file, 'r', encoding='utf-8') as infile:
        lines = infile.readlines()

    extracted_lines = []

    for line in lines:
        # 如果这一行是 JSON 格式的任务内容
        if '"completion"' in line:
            # 使用正则表达式提取代码部分
            match = re.search(code_pattern, line)
            if match:
                code_content = match.group(2)  # 只保留从 def 开始的代码
                # 使用 lambda 函数进行安全替换，避免字符串解析错误
                updated_line = re.sub(code_pattern, lambda m: m.group(1) + code_content + '"', line)
                extracted_lines.append(updated_line)
        else:
            extracted_lines.append(line)

    # 将提取后的内容写入新文件
    with open(output_file, 'w', encoding='utf-8') as outfile:
        outfile.writelines(extracted_lines)

# 调用函数
extract_and_save_code('/home/zhanghongyu/panruwei/acl/RQ2_results/samples_MoT_wo_modularization_HumanEval_deepseek.jsonl', '/home/zhanghongyu/panruwei/acl/RQ2_results/samples_MoT_wo_modularization_HumanEval_deepseek_re.jsonl')
