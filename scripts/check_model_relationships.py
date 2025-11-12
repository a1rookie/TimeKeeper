"""
Check Model Relationships
检查所有模型的双向关系是否正确配置
"""
import re
from pathlib import Path

models_dir = Path("app/models")
errors = []

# 收集所有relationship定义
relationships = {}  # {(ModelA, attr): (ModelB, back_attr)}

for model_file in models_dir.glob("*.py"):
    if model_file.name == "__init__.py":
        continue
    
    content = model_file.read_text(encoding="utf-8")
    
    # 查找class定义
    class_match = re.search(r'class (\w+)\(Base\):', content)
    if not class_match:
        continue
    
    model_name = class_match.group(1)
    
    # 查找所有relationship
    rel_pattern = r'(\w+)\s*=\s*relationship\(["\'](\w+)["\']\s*,\s*back_populates=["\'](\w+)["\']\s*[,)]'
    for match in re.finditer(rel_pattern, content):
        attr_name, target_model, back_attr = match.groups()
        relationships[(model_name, attr_name)] = (target_model, back_attr)

# 验证双向关系
print("=" * 70)
print("Checking Model Relationships...")
print("=" * 70)

for (model_a, attr_a), (model_b, back_attr_b) in relationships.items():
    # 检查反向关系是否存在
    reverse_key = (model_b, back_attr_b)
    
    if reverse_key not in relationships:
        error = f"ERROR: {model_a}.{attr_a} -> {model_b}.{back_attr_b} (MISSING REVERSE)"
        errors.append(error)
        print(f"   {error}")
        continue
    
    target_model_c, back_attr_c = relationships[reverse_key]
    
    # 检查反向关系是否指回正确的模型和属性
    if target_model_c != model_a or back_attr_c != attr_a:
        error = f"ERROR: {model_a}.{attr_a} <-> {model_b}.{back_attr_b} (MISMATCH: {model_b}.{back_attr_b} -> {target_model_c}.{back_attr_c})"
        errors.append(error)
        print(f"   {error}")
    else:
        print(f"   OK: {model_a}.{attr_a} <-> {model_b}.{back_attr_b}")

print("\n" + "=" * 70)
if errors:
    print(f"Found {len(errors)} errors!")
    for err in errors:
        print(f"  - {err}")
else:
    print("All relationships are correctly configured!")
print("=" * 70)
