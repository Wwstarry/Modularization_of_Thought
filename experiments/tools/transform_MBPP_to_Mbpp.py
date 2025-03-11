import json

# 打开jsonl文件进行读取和写入
input_file = '/home/zhanghongyu/panruwei/acl/samples_Self-planning_MBPP_gpt-4o-mini.jsonl'  # 输入文件路径
output_file = '/home/zhanghongyu/panruwei/acl/results/samples_Self-planning_MBPP_gpt-4o-mini.jsonl'  # 输出文件路径

# 打开输入文件并读取
with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
    for line in infile:
        # 解析JSON数据
        data = json.loads(line)
        
        # 替换"task_id"中的"MBPP"为"Mbpp"
        data["task_id"] = data["task_id"].replace("MBPP", "Mbpp")
        
        # 将修改后的数据写入到输出文件
        json.dump(data, outfile)
        outfile.write('\n')
