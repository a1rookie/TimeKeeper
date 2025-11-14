"""
修复路由返回值，统一使用 ApiResponse[T]
"""
from pathlib import Path


def fix_completions():
    """修复 completions.py"""
    file_path = Path("app/api/v1/completions.py")
    content = file_path.read_text(encoding="utf-8")
    
    # 添加 ApiResponse 导入
    if "from app.schemas.response import ApiResponse" not in content:
        content = content.replace(
            "from app.schemas.completion import (",
            "from app.schemas.response import ApiResponse\nfrom app.schemas.completion import ("
        )
    
    # 替换 response_model
    replacements = [
        # POST /completions
        ('response_model=ReminderCompletionResponse', 'response_model=ApiResponse[ReminderCompletionResponse]'),
        # GET /completions/reminder/{reminder_id}
        ('response_model=List[ReminderCompletionResponse]', 'response_model=ApiResponse[List[ReminderCompletionResponse]]'),
        # GET /stats/reminder/{reminder_id}
        ('response_model=ReminderStats', 'response_model=ApiResponse[ReminderStats]'),
        # GET /stats/my
        ('response_model=UserStats', 'response_model=ApiResponse[UserStats]'),
    ]
    
    for old, new in replacements:
        content = content.replace(old, new)
    
    # 修复返回语句 - 需要查找所有 return 语句并包装
    # 这个比较复杂，先输出提示让人工检查
    file_path.write_text(content, encoding="utf-8")
    print(f"[OK] 已更新 response_model: {file_path}")
    print("    [WARN] 需要手动检查返回语句是否用 ApiResponse.success() 包装")


def fix_debug():
    """修复 debug.py"""
    file_path = Path("app/api/v1/debug.py")
    content = file_path.read_text(encoding="utf-8")
    
    # 添加 ApiResponse 导入
    if "from app.schemas.response import ApiResponse" not in content:
        content = content.replace(
            "from app.core.config import settings",
            "from app.core.config import settings\nfrom app.schemas.response import ApiResponse"
        )
    
    # 添加 response_model
    # /health
    content = content.replace(
        '@router.get("/health")',
        '@router.get("/health", response_model=ApiResponse[dict])'
    )
    
    # /readiness
    content = content.replace(
        '@router.get("/readiness")',
        '@router.get("/readiness", response_model=ApiResponse[dict])'
    )
    
    file_path.write_text(content, encoding="utf-8")
    print(f"[OK] 已更新: {file_path}")
    print("    [WARN] 需要手动检查返回语句是否用 ApiResponse.success() 包装")


def fix_push_tasks():
    """修复 push_tasks.py"""
    file_path = Path("app/api/v1/push_tasks.py")
    content = file_path.read_text(encoding="utf-8")
    
    # 添加 ApiResponse 导入
    if "from app.schemas.response import ApiResponse" not in content:
        content = content.replace(
            "from app.schemas.push_task import (",
            "from app.schemas.response import ApiResponse\nfrom app.schemas.push_task import ("
        )
    
    # 替换 response_model
    replacements = [
        ('response_model=PushTaskList', 'response_model=ApiResponse[PushTaskList]'),
        ('response_model=PushTaskResponse', 'response_model=ApiResponse[PushTaskResponse]'),
    ]
    
    for old, new in replacements:
        content = content.replace(old, new)
    
    # /stats/summary 没有 response_model
    content = content.replace(
        '@router.get("/stats/summary")',
        '@router.get("/stats/summary", response_model=ApiResponse[dict])'
    )
    
    file_path.write_text(content, encoding="utf-8")
    print(f"[OK] 已更新: {file_path}")
    print("    [WARN] 需要手动检查返回语句是否用 ApiResponse.success() 包装")


def fix_templates():
    """修复 templates.py"""
    file_path = Path("app/api/v1/templates.py")
    content = file_path.read_text(encoding="utf-8")
    
    # 添加 ApiResponse 导入
    if "from app.schemas.response import ApiResponse" not in content:
        content = content.replace(
            "from app.schemas.template import (",
            "from app.schemas.response import ApiResponse\nfrom app.schemas.template import ("
        )
    
    # 替换所有 response_model
    replacements = [
        ('response_model=List[ReminderTemplateResponse]', 'response_model=ApiResponse[List[ReminderTemplateResponse]]'),
        ('response_model=ReminderTemplateResponse', 'response_model=ApiResponse[ReminderTemplateResponse]'),
        ('response_model=UserCustomTemplateResponse', 'response_model=ApiResponse[UserCustomTemplateResponse]'),
        ('response_model=List[UserCustomTemplateResponse]', 'response_model=ApiResponse[List[UserCustomTemplateResponse]]'),
        ('response_model=TemplateShareResponse', 'response_model=ApiResponse[TemplateShareResponse]'),
        ('response_model=List[TemplateShareResponse]', 'response_model=ApiResponse[List[TemplateShareResponse]]'),
        ('response_model=TemplateShareDetail', 'response_model=ApiResponse[TemplateShareDetail]'),
        ('response_model=TemplateUsageResponse', 'response_model=ApiResponse[TemplateUsageResponse]'),
    ]
    
    for old, new in replacements:
        content = content.replace(old, new)
    
    file_path.write_text(content, encoding="utf-8")
    print(f"[OK] 已更新: {file_path}")
    print("    [WARN] 需要手动检查返回语句是否用 ApiResponse.success() 包装")


def main():
    print("=" * 60)
    print("开始修复 API 返回格式...")
    print("=" * 60)
    
    fix_completions()
    fix_debug()
    fix_push_tasks()
    fix_templates()
    
    print("\n" + "=" * 60)
    print("response_model 已全部更新！")
    print("=" * 60)
    print("\n[重要] 接下来需要手动修复返回语句:")
    print("  1. 将所有 'return xxx' 改为 'return ApiResponse.success(data=xxx)'")
    print("  2. 或者使用正则批量替换")
    print("  3. 确保所有端点都返回统一格式\n")


if __name__ == "__main__":
    main()
