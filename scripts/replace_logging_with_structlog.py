"""
替换所有文件中的logging为structlog
"""
import re
from pathlib import Path

def replace_logging_in_file(file_path: Path):
    """替换单个文件中的logging调用"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 1. 替换导入语句
        # import logging -> import structlog
        if 'import logging' in content and 'structlog' not in content:
            # 如果只有 import logging，直接替换
            content = re.sub(
                r'^import logging$',
                'import structlog',
                content,
                flags=re.MULTILINE
            )
        
        # 2. 替换 logger = logging.getLogger(__name__)
        content = re.sub(
            r'logger = logging\.getLogger\(__name__\)',
            'logger = structlog.get_logger(__name__)',
            content
        )
        
        # 3. 替换 logger = logging.getLogger("xxx")
        content = re.sub(
            r'logger = logging\.getLogger\(["\']([^"\']+)["\']\)',
            r'logger = structlog.get_logger("\1")',
            content
        )
        
        # 4. 替换 logging.getLogger() 直接调用
        content = re.sub(
            r'logging\.getLogger\(\)',
            'structlog.get_logger()',
            content
        )
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✓ 已更新: {file_path}")
            return True
        return False
        
    except Exception as e:
        print(f"✗ 处理失败 {file_path}: {e}")
        return False

def main():
    base_dir = Path(__file__).parent.parent
    app_dir = base_dir / "app"
    
    # 查找所有Python文件
    python_files = list(app_dir.rglob("*.py"))
    
    # 也包括main.py
    if (base_dir / "main.py").exists():
        python_files.append(base_dir / "main.py")
    
    updated_count = 0
    for file_path in python_files:
        # 跳过__pycache__
        if '__pycache__' in str(file_path):
            continue
        
        if replace_logging_in_file(file_path):
            updated_count += 1
    
    print(f"\n总计更新了 {updated_count} 个文件")
    print("\n注意: logging_config.py 已手动配置，请检查其他特殊情况")

if __name__ == "__main__":
    main()
