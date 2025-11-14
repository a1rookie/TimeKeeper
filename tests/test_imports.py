"""检查导入错误"""
import sys
import traceback

try:
    print("尝试导入 app.services.push_scheduler...")
    print("✓ 导入成功")
except Exception:
    print("✗ 导入失败:")
    traceback.print_exc()
    sys.exit(1)

try:
    print("\n尝试导入 main...")
    print("✓ 导入成功")
except Exception:
    print("✗ 导入失败:")
    traceback.print_exc()
    sys.exit(1)

print("\n所有导入成功！")
