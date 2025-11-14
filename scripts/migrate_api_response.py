"""
API 响应格式自动迁移脚本
Automatically migrate API endpoints to use unified ApiResponse format
"""
import re
import sys
from pathlib import Path

def migrate_file(file_path: Path):
    """迁移单个文件"""
    print(f"正在迁移: {file_path.name}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否已经导入 ApiResponse
    if 'from app.schemas.response import ApiResponse' not in content:
        # 在导入区域添加
        import_pattern = r'(from fastapi import [^\n]+\n)'
        content = re.sub(
            import_pattern,
            r'\1from app.schemas.response import ApiResponse\n',
            content,
            count=1
        )
        print("  ✓ 添加 ApiResponse 导入")
    
    # 统计修改次数
    changes = 0
    
    # 模式1: response_model=XxxResponse -> response_model=ApiResponse[XxxResponse]
    pattern1 = r'response_model=(\w+)(?![\[\]])'
    matches1 = re.findall(pattern1, content)
    for match in set(matches1):
        if match != 'ApiResponse':  # 跳过已经是 ApiResponse 的
            content = re.sub(
                f'response_model={match}(?![\[\]])',
                f'response_model=ApiResponse[{match}]',
                content
            )
            changes += 1
    
    # 模式2: response_model=List[XxxResponse] -> response_model=ApiResponse[List[XxxResponse]]
    pattern2 = r'response_model=(List\[\w+\])(?![,\]])'
    matches2 = re.findall(pattern2, content)
    for match in set(matches2):
        content = re.sub(
            f'response_model={re.escape(match)}(?![,\]])',
            f'response_model=ApiResponse[{match}]',
            content
        )
        changes += 1
    
    # 模式3: status_code=status.HTTP_204_NO_CONTENT -> response_model=ApiResponse[None]
    # 找到所有 DELETE 接口，添加 response_model
    delete_pattern = r'@router\.delete\([^)]+\)(?!\s*,\s*response_model)'
    content = re.sub(
        delete_pattern,
        lambda m: m.group(0).replace(')', ', response_model=ApiResponse[None])'),
        content
    )
    
    # 检查是否有简单的 return 语句需要包装
    # 这部分较复杂，需要手动检查
    
    if changes > 0:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✓ 完成 {changes} 处修改")
        return True
    else:
        print("  ⊘ 无需修改")
        return False

def main():
    """主函数"""
    # 获取 API 路由目录
    api_dir = Path(__file__).parent.parent / 'app' / 'api' / 'v1'
    
    if not api_dir.exists():
        print(f"错误: 找不到目录 {api_dir}")
        sys.exit(1)
    
    # 需要迁移的文件列表
    files_to_migrate = [
        'completions.py',
        'templates.py',
        'push_tasks.py',
        'debug.py'
    ]
    
    print("=" * 60)
    print("API 响应格式迁移工具")
    print("=" * 60)
    print()
    
    migrated_count = 0
    for filename in files_to_migrate:
        file_path = api_dir / filename
        if file_path.exists():
            if migrate_file(file_path):
                migrated_count += 1
        else:
            print(f"警告: 文件不存在 {filename}")
        print()
    
    print("=" * 60)
    print(f"迁移完成! 共处理 {migrated_count}/{len(files_to_migrate)} 个文件")
    print("=" * 60)
    print()
    print("⚠️  注意:")
    print("1. 自动迁移只修改了 response_model 声明")
    print("2. 需要手动修改每个接口的 return 语句")
    print("3. 将 'return data' 改为 'return ApiResponse.success(data=data)'")
    print("4. 参考已迁移文件: users.py, reminders.py, family.py")

if __name__ == '__main__':
    main()
