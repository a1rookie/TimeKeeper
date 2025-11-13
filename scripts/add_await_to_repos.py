"""
为所有repository调用添加await
"""
import re
from pathlib import Path

# 需要修改的文件
files_to_fix = [
    "app/api/v1/completions.py",
    "app/api/v1/templates.py",
    "app/api/v1/push_tasks.py",
    "app/api/v1/debug.py"
]

def add_await_to_repo_calls(file_path: Path):
    """为repository调用添加await"""
    print(f"\n修复文件: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    modified_lines = []
    changes_count = 0
    
    for i, line in enumerate(lines):
        # 检查是否包含 _repo. 调用，且前面没有 await
        # 匹配模式: xxx_repo.method(...) 且前面没有 await
        if re.search(r'_repo\.(get|create|update|delete|add|mark|is_|count|deactivate|remove)', line):
            # 检查前面是否已经有 await
            if 'await ' not in line:
                # 在赋值语句或表达式前添加 await
                # 匹配 = xxx_repo. 或 if xxx_repo. 等
                if '=' in line or 'if ' in line or 'return ' in line:
                    # 找到 _repo. 的位置，在前面添加 await
                    modified_line = re.sub(
                        r'(\s+)(.*?)(\w+_repo\.)',
                        r'\1\2await \3',
                        line
                    )
                    if modified_line != line:
                        modified_lines.append(modified_line)
                        changes_count += 1
                        print(f"  行 {i+1}: 添加 await")
                    else:
                        modified_lines.append(line)
                else:
                    modified_lines.append(line)
            else:
                modified_lines.append(line)
        else:
            modified_lines.append(line)
    
    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(modified_lines)
    
    print(f"✓ 已修复: {file_path} ({changes_count} 处修改)")

def main():
    base_dir = Path(__file__).parent.parent
    
    total_changes = 0
    for file_rel_path in files_to_fix:
        file_path = base_dir / file_rel_path
        if file_path.exists():
            try:
                add_await_to_repo_calls(file_path)
            except Exception as e:
                print(f"✗ 修复失败 {file_path}: {e}")
        else:
            print(f"✗ 文件不存在: {file_path}")
    
    print("\n完成!")
    print("请手动检查文件确保await添加正确")

if __name__ == "__main__":
    main()
