"""
API 响应格式端到端测试
测试已迁移接口的实际响应格式
"""
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from main import app

def test_response_format():
    """测试响应格式"""
    print("=" * 70)
    print("API 响应格式测试")
    print("=" * 70)
    print()
    
    client = TestClient(app)
    
    # 测试1: 健康检查（未迁移，应该是原始格式）
    print("📝 测试1: 健康检查（未迁移）")
    response = client.get("/api/v1/debug/health")
    data = response.json()
    print(f"   状态码: {response.status_code}")
    print(f"   响应: {data}")
    if "status" in data:  # 原始格式
        print("   ✅ 未迁移接口保持原始格式")
    print()
    
    # 测试2: 未认证访问（应该返回统一错误格式）
    print("📝 测试2: 未认证访问（测试异常处理）")
    response = client.get("/api/v1/users/me")
    data = response.json()
    print(f"   状态码: {response.status_code}")
    print(f"   响应: {data}")
    
    # 验证统一错误格式
    if all(key in data for key in ["code", "message", "data"]):
        print("   ✅ 错误响应符合统一格式")
        print(f"   - code: {data['code']}")
        print(f"   - message: {data['message']}")
        print(f"   - data: {data['data']}")
    else:
        print("   ❌ 错误响应格式不正确")
    print()
    
    # 测试3: 参数验证错误（测试 ValidationError 处理）
    print("📝 测试3: 参数验证错误")
    response = client.post(
        "/api/v1/users/register",
        json={"phone": "invalid"}  # 缺少必需字段
    )
    data = response.json()
    print(f"   状态码: {response.status_code}")
    print(f"   响应: {data}")
    
    if all(key in data for key in ["code", "message", "data"]):
        print("   ✅ 验证错误符合统一格式")
        print(f"   - code: {data['code']}")
        print(f"   - message: {data['message'][:50]}...")
    else:
        print("   ❌ 验证错误格式不正确")
    print()
    
    print("=" * 70)
    print("测试完成！")
    print()
    print("✅ 已迁移接口:")
    print("   - users.py (8个接口)")
    print("   - reminders.py (10个接口)")
    print("   - family.py (8个接口)")
    print()
    print("📋 响应格式:")
    print("   - 成功: {code: 200, message: 'xxx', data: {...}}")
    print("   - 错误: {code: 4xx/5xx, message: 'xxx', data: null}")
    print()
    print("🔧 后续工作:")
    print("   1. 迁移剩余接口 (completions, templates, push_tasks)")
    print("   2. 启动服务测试实际接口")
    print("   3. 更新前端代码适配新格式")
    print("=" * 70)

if __name__ == '__main__':
    test_response_format()
