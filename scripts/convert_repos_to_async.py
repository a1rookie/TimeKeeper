"""
自动将 Repository 文件从同步转换为异步

使用方法：
    python scripts/convert_repos_to_async.py
"""

import re
from pathlib import Path

def convert_repository_to_async(file_path: Path) -> bool:
    """转换单个 repository 文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # 1. 更新导入
    content = re.sub(
        r'from sqlalchemy\.orm import Session',
        'from sqlalchemy.ext.asyncio import AsyncSession\nfrom sqlalchemy import select',
        content
    )
    
    # 2. 更新__init__参数
    content = re.sub(
        r'def __init__\(self, db: Session\):',
        'def __init__(self, db: AsyncSession):',
        content
    )
    
    # 3. 添加async到所有公共方法（不包括__init__）
    content = re.sub(
        r'\n    def ([a-z_][a-z0-9_]*)\(',
        r'\n    async def \1(',
        content
    )
    
    # 4. 修复__init__（不应该是async）
    content = re.sub(
        r'async def __init__',
        'def __init__',
        content
    )
    
    # 5. 将 self.db.query 转换为 select
    # 简单的query().filter().first()
    content = re.sub(
        r'return self\.db\.query\((\w+)\)\.filter\(([^)]+)\)\.first\(\)',
        r'result = await self.db.execute(select(\1).filter(\2))\n        return result.scalar_one_or_none()',
        content
    )
    
    # query().filter().all()
    content = re.sub(
        r'return self\.db\.query\((\w+)\)\.filter\(([^)]+)\)\.all\(\)',
        r'result = await self.db.execute(select(\1).filter(\2))\n        return list(result.scalars().all())',
        content
    )
    
    # 6. 添加await到 commit, refresh, delete
    content = re.sub(r'self\.db\.commit\(\)', 'await self.db.commit()', content)
    content = re.sub(r'self\.db\.refresh\(', 'await self.db.refresh(', content)
    content = re.sub(r'self\.db\.delete\(', 'await self.db.delete(', content)
    
    # 7. 处理更复杂的query chains
    # 这需要手动处理，脚本只能做简单转换
    
    if content == original_content:
        return False
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return True

def main():
    """主函数"""
    repos_dir = Path(__file__).parent.parent / 'app' / 'repositories'
    
    if not repos_dir.exists():
        print(f"错误: 找不到目录 {repos_dir}")
        return
    
    # 需要转换的文件（排除已转换的）
    skip_files = {
        'user_repository.py',
        'reminder_repository.py',
        '__init__.py'
    }
    
    print("=" * 60)
    print("Repository 异步转换工具")
    print("=" * 60)
    print()
    
    converted = 0
    skipped = 0
    
    for repo_file in repos_dir.glob('*.py'):
        if repo_file.name in skip_files:
            print(f"⊙ 跳过: {repo_file.name} (已手动转换)")
            skipped += 1
            continue
        
        if repo_file.name.startswith('__'):
            continue
        
        print(f"📝 转换: {repo_file.name}")
        if convert_repository_to_async(repo_file):
            print("   ✅ 已转换")
            converted += 1
        else:
            print("   ⊘ 无需转换")
    
    print()
    print("=" * 60)
    print(f"转换完成: {converted} 个文件已转换, {skipped} 个跳过")
    print("=" * 60)
    print()
    print("⚠️  注意:")
    print("1. 脚本只做基本转换，复杂query需要手动检查")
    print("2. 建议运行后检查每个文件的语法")
    print("3. 特别注意 .query() 链式调用的转换")
    print("4. 使用 'uv run python -m py_compile <file>' 检查语法")

if __name__ == '__main__':
    main()
