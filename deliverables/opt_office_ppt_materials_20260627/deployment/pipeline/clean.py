# 定义文件路径
input_file_path = '/cpfs01/projects-HDD/cfff-4da39d3c1e4e_HDD/cyl_23110240101/opt/128m/10000.txt'
output_file_path = '/cpfs01/projects-HDD/cfff-4da39d3c1e4e_HDD/cyl_23110240101/opt/128m/10000_cl.txt'

# 打开输入文件并读取内容
with open(input_file_path, 'r', encoding='utf-8') as infile, \
     open(output_file_path, 'w', encoding='utf-8') as outfile:
    
    for line in infile:
        # 去掉每行前半部分，保留空格后的内容
        # 使用split方法分割行，并获取第二部分
        password = line.split('\t')[-1].strip()  # 取最后一部分并去掉前后空格
        outfile.write(f"{password}\n")  # 写入输出文件

print("密码清理完成，已保存到:", output_file_path)
