import os

# 定义测试文件路径和生成的密码文件路径
TEST_FILE = "/cpfs01/projects-HDD/cfff-4da39d3c1e4e_HDD/cyl_23110240101/PagPassGPT1/dataset/rockyou-cleaned.txt"
GEN_PASSWORD_FILE = "/cpfs01/projects-HDD/cfff-4da39d3c1e4e_HDD/cyl_23110240101/opt/128m/10000_cl.txt"

def get_gen_passwords(gen_file):
    """ 从生成文件中提取密码 """
    gen_passwords = []
    # 加 encoding="latin-1"，兼容原文件写入编码
    with open(gen_file, "r", encoding="latin-1") as f:
        for line in f.readlines():
            gen_passwords.append(line.strip())  # 移除换行符
    return gen_passwords

def get_hit_rate(test_file, gen_file):
    """ 计算命中率 """
    hit_num = 0
    gen_passwords = get_gen_passwords(gen_file)
    gen_passwords = set(gen_passwords)  # 使用集合去重

    # 不确定 test_file 编码，通常可用默认，如遇类似错误也可换成 encoding="latin-1"
    with open(test_file, "r") as f:
        test_passwords = {line.strip() for line in f.readlines()}  # 使用集合存储测试密码

    for password in gen_passwords:
        if password in test_passwords:
            hit_num += 1
    
    hit_rate = hit_num / len(test_passwords) if test_passwords else 0  # 防止除以零
    return hit_rate

def get_repeat_rate(gen_file):
    """ 计算重复率 """
    gen_passwords = get_gen_passwords(gen_file)
    unique_gen_passwords = set(gen_passwords)
    repeat_rate = 1 - len(unique_gen_passwords) / len(gen_passwords) if gen_passwords else 0  # 防止除以零
    return repeat_rate

# 计算命中率和重复率
hit_rate = get_hit_rate(TEST_FILE, GEN_PASSWORD_FILE)
repeat_rate = get_repeat_rate(GEN_PASSWORD_FILE)

# 打印结果
print("Hit Rate: ", hit_rate)
print("Repeat Rate: ", repeat_rate)