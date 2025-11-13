"""
快速修复剩余路由文件的异步问题
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

def fix_route_file(file_path: Path):
    """修复单个路由文件"""
    print(f"\n修复文件: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. 替换 Session 导入为 AsyncSession
    content = re.sub(
        r'from sqlalchemy\.orm import Session',
        'from sqlalchemy.ext.asyncio import AsyncSession',
        content
    )
    
    # 2. 替换函数定义中的 db: Session 为 db: AsyncSession
    content = re.sub(
        r'(\s+)db: Session = Depends\(get_db\)',
        r'\1db: AsyncSession = Depends(get_db)',
        content
    )
    
    # 3. 将所有非async的路由函数改为async
    # 匹配 @router.xxx 后面的 def 函数
    content = re.sub(
        r'(@router\.(get|post|put|delete|patch)\([^\)]+\)\s*\n)def ',
        r'\1async def ',
        content,
        flags=re.MULTILINE
    )
    
    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✓ 已修复: {file_path}")

def main():
    base_dir = Path(__file__).parent.parent
    
    for file_rel_path in files_to_fix:
        file_path = base_dir / file_rel_path
        if file_path.exists():
            try:
                fix_route_file(file_path)
            except Exception as e:
                print(f"✗ 修复失败 {file_path}: {e}")
        else:
            print(f"✗ 文件不存在: {file_path}")
    
    print("\n完成!")
    print("\n注意: 脚本只修改了函数签名和Session参数")
    print("还需要手动在repository调用前添加 await")

if __name__ == "__main__":
    main()
