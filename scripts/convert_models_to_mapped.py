"""
Convert SQLAlchemy models from Column syntax to Mapped syntax
将 SQLAlchemy 模型从 Column 语法转换为 Mapped 语法
"""

import re
from pathlib import Path

def convert_model_file(file_path: Path):
    """转换单个模型文件"""
    print(f"Converting {file_path.name}...")
    
    content = file_path.read_text(encoding='utf-8')
    
    # 跳过已经转换过的文件
    if 'Mapped[' in content:
        print("  ✓ Already converted")
        return
    
    # 替换 import 语句
    content = re.sub(
        r'from sqlalchemy import ([^\n]+)',
        lambda m: replace_imports(m.group(1)),
        content
    )
    
    # 添加类型导入
    if 'from typing import' not in content:
        content = content.replace(
            'from sqlalchemy',
            'from typing import Optional, List, Dict, Any\nfrom datetime import datetime\nfrom sqlalchemy',
            1
        )
    
    # 替换 Column 定义
    content = convert_columns(content)
    
    # 替换 relationship 定义
    content = convert_relationships(content)
    
    file_path.write_text(content, encoding='utf-8')
    print("  ✓ Converted successfully")

def replace_imports(import_str: str) -> str:
    """替换 import 语句"""
    # 移除不需要的导入
    removes = ['Column', 'Integer', 'Boolean', 'DateTime', 'JSON']
    parts = [p.strip() for p in import_str.split(',')]
    filtered = [p for p in parts if p not in removes]
    
    # 添加 func 如果不存在
    if 'func' not in filtered:
        filtered.append('func')
    
    # 添加 Mapped 相关导入
    result = 'from sqlalchemy import ' + ', '.join(filtered) + '\n'
    result += 'from sqlalchemy.orm import Mapped, mapped_column, relationship'
    
    return result

def convert_columns(content: str) -> str:
    """转换 Column 定义为 Mapped"""
    lines = content.split('\n')
    new_lines = []
    
    for line in lines:
        if '= Column(' in line and 'Mapped' not in line:
            new_line = convert_column_line(line)
            new_lines.append(new_line)
        else:
            new_lines.append(line)
    
    return '\n'.join(new_lines)

def convert_column_line(line: str) -> str:
    """转换单行 Column 定义"""
    indent = len(line) - len(line.lstrip())
    indent_str = ' ' * indent
    
    # 提取字段名
    match = re.search(r'(\w+)\s*=\s*Column\((.*)\)', line)
    if not match:
        return line
    
    field_name = match.group(1)
    column_args = match.group(2)
    
    # 判断类型和是否可选
    is_optional = 'nullable=True' in column_args or ', nullable=True' in column_args
    is_list = 'JSON' in column_args and ('default=[]' in column_args or 'default=list' in column_args)
    is_dict = 'JSON' in column_args and ('default={}' in column_args or 'default=dict' in column_args)
    
    # 确定 Python 类型
    if 'Integer' in column_args and 'ForeignKey' not in column_args and 'primary_key' not in column_args:
        py_type = 'Optional[int]' if is_optional else 'int'
    elif 'String' in column_args:
        py_type = 'Optional[str]' if is_optional else 'str'
    elif 'Boolean' in column_args:
        py_type = 'Optional[bool]' if is_optional else 'bool'
    elif 'DateTime' in column_args:
        py_type = 'Optional[datetime]' if is_optional else 'datetime'
    elif is_list:
        py_type = 'Optional[List[Dict[str, Any]]]' if is_optional else 'List[Dict[str, Any]]'
    elif is_dict:
        py_type = 'Optional[Dict[str, Any]]' if is_optional else 'Dict[str, Any]'
    elif 'primary_key=True' in column_args or 'ForeignKey' in column_args:
        py_type = 'Optional[int]' if is_optional else 'int'
    else:
        py_type = 'Optional[Any]' if is_optional else 'Any'
    
    # 清理 column_args
    column_args = column_args.replace('Integer', '')
    column_args = column_args.replace('Boolean', '')
    column_args = column_args.replace('DateTime(timezone=True)', '')
    column_args = column_args.replace('JSON', '')
    column_args = re.sub(r',\s*nullable=\w+', '', column_args)
    column_args = re.sub(r'nullable=\w+,?\s*', '', column_args)
    column_args = column_args.strip().strip(',').strip()
    
    # 构建新行
    if column_args:
        new_line = f'{indent_str}{field_name}: Mapped[{py_type}] = mapped_column({column_args})'
    else:
        new_line = f'{indent_str}{field_name}: Mapped[{py_type}] = mapped_column()'
    
    return new_line

def convert_relationships(content: str) -> str:
    """转换 relationship 定义"""
    lines = content.split('\n')
    new_lines = []
    
    for line in lines:
        if '= relationship(' in line and 'Mapped' not in line:
            new_line = convert_relationship_line(line)
            new_lines.append(new_line)
        else:
            new_lines.append(line)
    
    return '\n'.join(new_lines)

def convert_relationship_line(line: str) -> str:
    """转换单行 relationship 定义"""
    indent = len(line) - len(line.lstrip())
    indent_str = ' ' * indent
    
    match = re.search(r'(\w+)\s*=\s*relationship\(\"(\w+)\"', line)
    if not match:
        return line
    
    field_name = match.group(1)
    related_model = match.group(2)
    
    # 判断是否是集合
    is_collection = 'cascade=' in line or field_name.endswith('s')
    
    if is_collection:
        py_type = f'List["{related_model}"]'
    else:
        # 检查是否可选
        is_optional = 'nullable=True' in line or 'Optional' in related_model
        py_type = f'Optional["{related_model}"]' if is_optional or related_model.lower() in field_name else f'"{related_model}"'
    
    rest_of_line = line.split('= relationship(')[1]
    new_line = f'{indent_str}{field_name}: Mapped[{py_type}] = relationship({rest_of_line}'
    
    return new_line

if __name__ == '__main__':
    models_dir = Path(__file__).parent / 'app' / 'models'
    
    for model_file in models_dir.glob('*.py'):
        if model_file.name == '__init__.py':
            continue
        
        try:
            convert_model_file(model_file)
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    print("\n✓ Conversion complete!")
