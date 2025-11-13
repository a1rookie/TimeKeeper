"""
API 响应格式迁移验证脚本
检查已迁移文件的迁移质量
"""
import re
from pathlib import Path
from typing import List, Dict

def check_file(file_path: Path) -> Dict:
    """检查单个文件的迁移质量"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    issues = []
    stats = {
        'file': file_path.name,
        'has_import': False,
        'endpoints_count': 0,
        'migrated_endpoints': 0,
        'issues': issues
    }
    
    # 检查是否导入 ApiResponse
    if 'from app.schemas.response import ApiResponse' in content:
        stats['has_import'] = True
    else:
        issues.append('❌ 未导入 ApiResponse')
    
    # 统计接口数量
    endpoints = re.findall(r'@router\.(get|post|put|delete|patch)', content)
    stats['endpoints_count'] = len(endpoints)
    
    # 检查 response_model 迁移
    migrated_models = re.findall(r'response_model=ApiResponse\[', content)
    stats['migrated_endpoints'] = len(migrated_models)
    
    # 检查是否有未迁移的 response_model
    unmigrated = re.findall(r'response_model=(?!ApiResponse)(\w+)', content)
    if unmigrated:
        issues.append(f'⚠️  发现未迁移的 response_model: {set(unmigrated)}')
    
    # 检查是否有 return ApiResponse.success
    success_returns = len(re.findall(r'return ApiResponse\.success', content))
    if success_returns < stats['migrated_endpoints']:
        issues.append(f'⚠️  return 语句可能未完全迁移 (期望{stats["migrated_endpoints"]}, 发现{success_returns})')
    
    # 检查是否有 204 状态码（DELETE 接口应该用 ApiResponse[None]）
    if 'HTTP_204_NO_CONTENT' in content:
        issues.append('⚠️  仍使用 HTTP_204_NO_CONTENT，建议改用 ApiResponse[None]')
    
    return stats

def main():
    """主函数"""
    print("=" * 70)
    print("API 响应格式迁移验证")
    print("=" * 70)
    print()
    
    # 检查已迁移的文件
    api_dir = Path(__file__).parent.parent / 'app' / 'api' / 'v1'
    migrated_files = [
        'users.py',
        'reminders.py',
        'family.py'
    ]
    
    total_endpoints = 0
    total_migrated = 0
    all_issues = []
    
    for filename in migrated_files:
        file_path = api_dir / filename
        if not file_path.exists():
            print(f"❌ 文件不存在: {filename}")
            continue
        
        stats = check_file(file_path)
        total_endpoints += stats['endpoints_count']
        total_migrated += stats['migrated_endpoints']
        
        # 打印结果
        print(f"📄 {filename}")
        print(f"   ✓ 接口总数: {stats['endpoints_count']}")
        print(f"   ✓ 已迁移: {stats['migrated_endpoints']}")
        
        if stats['has_import']:
            print(f"   ✓ 已导入 ApiResponse")
        
        if stats['issues']:
            for issue in stats['issues']:
                print(f"   {issue}")
        else:
            print(f"   ✅ 无问题")
        
        print()
        
        all_issues.extend(stats['issues'])
    
    # 总结
    print("=" * 70)
    print(f"总计: {total_migrated}/{total_endpoints} 个接口已迁移")
    
    if all_issues:
        print(f"\n⚠️  发现 {len(all_issues)} 个问题需要关注")
    else:
        print("\n✅ 所有检查通过！")
    
    print("=" * 70)

if __name__ == '__main__':
    main()
