"""
批量更新路由文件为异步

1. 替换 Session 为 AsyncSession
2. 在所有 repository 调用前添加 await
3. 在所有 db.commit/refresh/delete 前添加 await
"""

import re
from pathlib import Path

def update_route_file(file_path: Path) -> bool:
    """更新单个路由文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        # 尝试使用其他编码
        with open(file_path, 'r', encoding='gbk') as f:
            content = f.read()
    
    original_content = content
    
    # 1. 替换导入
    if 'from sqlalchemy.orm import Session' in content:
        content = content.replace(
            'from sqlalchemy.orm import Session',
            'from sqlalchemy.ext.asyncio import AsyncSession'
        )
    
    # 2. 替换参数类型
    content = re.sub(
        r'db: Session = Depends\(',
        'db: AsyncSession = Depends(',
        content
    )
    
    # 3. 在repository方法调用前添加await（保守的模式）
    # reminder_repo.xxx(...) -> await reminder_repo.xxx(...)
    content = re.sub(
        r'([^await ])([\w_]+_repo)\.(\w+)\(',
        r'\1await \2.\3(',
        content
    )
    
    # 4. 在db方法前添加await
    content = re.sub(r'(\s+)(db\.commit\(\))', r'\1await \2', content)
    content = re.sub(r'(\s+)(db\.refresh\()', r'\1await \2', content)
    content = re.sub(r'(\s+)(db\.delete\()', r'\1await \2', content)
    content = re.sub(r'(\s+)(db\.add\()', r'\1\2', content)  # add不需要await
    
    # 5. 修复重复的await await
    content = re.sub(r'await await', 'await', content)
    
    if content == original_content:
        return False
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return True

def main():
    """主函数"""
    api_dir = Path(__file__).parent.parent / 'app' / 'api' / 'v1'
    
    # 需要更新的路由文件
    route_files = [
        'users.py',
        'reminders.py',
        'family.py',
        'completions.py',
        'templates.py',
        'push_tasks.py',
        'debug.py'
    ]
    
    print("=" * 60)
    print("路由文件异步更新工具")
    print("=" * 60)
    print()
    
    updated = 0
    for filename in route_files:
        file_path = api_dir / filename
        if not file_path.exists():
            print(f"⊙ 跳过: {filename} (文件不存在)")
            continue
        
        print(f"📝 处理: {filename}")
        if update_route_file(file_path):
            print(f"   ✅ 已更新")
            updated += 1
        else:
            print(f"   ⊘ 无需更新")
    
    print()
    print("=" * 60)
    print(f"更新完成: {updated} 个文件已更新")
    print("=" * 60)
    print()
    print("⚠️  注意:")
    print("1. 脚本可能会漏掉一些复杂的调用")
    print("2. 建议手动检查每个文件")
    print("3. 特别检查 await 是否添加正确")
    print("4. 运行应用测试是否工作正常")

if __name__ == '__main__':
    main()
