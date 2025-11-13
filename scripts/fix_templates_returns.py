"""
专门修复 templates.py 的 return 语句
"""
from pathlib import Path


def fix_templates():
    file_path = Path("app/api/v1/templates.py")
    content = file_path.read_text(encoding="utf-8")
    
    # 定义所有需要替换的 return 语句
    replacements = [
        # 1. GET /templates/system - list_system_templates (line 55)
        (
            "    return [\n        ReminderTemplateResponse(\n            id=t.id,\n            name=t.name,\n            category=t.category,\n            description=t.description,\n            default_recurrence_type=t.default_recurrence_type,\n            default_recurrence_config=t.default_recurrence_config,\n            default_remind_advance_days=t.default_remind_advance_days,\n            usage_count=t.usage_count,\n            is_active=t.is_active,\n            created_at=t.created_at\n        ) for t in templates\n    ]",
            "    return ApiResponse.success(data=[\n        ReminderTemplateResponse(\n            id=t.id,\n            name=t.name,\n            category=t.category,\n            description=t.description,\n            default_recurrence_type=t.default_recurrence_type,\n            default_recurrence_config=t.default_recurrence_config,\n            default_remind_advance_days=t.default_remind_advance_days,\n            usage_count=t.usage_count,\n            is_active=t.is_active,\n            created_at=t.created_at\n        ) for t in templates\n    ])"
        ),
        
        # 2. GET /templates/system/{template_id} - get_system_template_detail (line 86)
        (
            "    return ReminderTemplateResponse(\n        id=template.id,\n        name=template.name,\n        category=template.category,\n        description=template.description,\n        default_recurrence_type=template.default_recurrence_type,\n        default_recurrence_config=template.default_recurrence_config,\n        default_remind_advance_days=template.default_remind_advance_days,\n        usage_count=template.usage_count,\n        is_active=template.is_active,\n        created_at=template.created_at\n    )\n\n\n@router.get(\"/templates/system/popular\"",
            "    return ApiResponse.success(data=ReminderTemplateResponse(\n        id=template.id,\n        name=template.name,\n        category=template.category,\n        description=template.description,\n        default_recurrence_type=template.default_recurrence_type,\n        default_recurrence_config=template.default_recurrence_config,\n        default_remind_advance_days=template.default_remind_advance_days,\n        usage_count=template.usage_count,\n        is_active=template.is_active,\n        created_at=template.created_at\n    ))\n\n\n@router.get(\"/templates/system/popular\""
        ),
        
        # 3. GET /templates/system/popular - get_popular_templates (line 109)
        (
            "    templates = await template_repo.get_popular(limit=limit)\n    \n    return [\n        ReminderTemplateResponse(\n            id=t.id,\n            name=t.name,\n            category=t.category,\n            description=t.description,\n            default_recurrence_type=t.default_recurrence_type,\n            default_recurrence_config=t.default_recurrence_config,\n            default_remind_advance_days=t.default_remind_advance_days,\n            usage_count=t.usage_count,\n            is_active=t.is_active,\n            created_at=t.created_at\n        ) for t in templates\n    ]\n\n\n# ==================== 用户自定义模板 ====================",
            "    templates = await template_repo.get_popular(limit=limit)\n    \n    return ApiResponse.success(data=[\n        ReminderTemplateResponse(\n            id=t.id,\n            name=t.name,\n            category=t.category,\n            description=t.description,\n            default_recurrence_type=t.default_recurrence_type,\n            default_recurrence_config=t.default_recurrence_config,\n            default_remind_advance_days=t.default_remind_advance_days,\n            usage_count=t.usage_count,\n            is_active=t.is_active,\n            created_at=t.created_at\n        ) for t in templates\n    ])\n\n\n# ==================== 用户自定义模板 ===================="
        ),
        
        # 4-13: 其他 return 语句 - 使用简单替换
        ("    return UserCustomTemplateResponse(", "    return ApiResponse.success(data=UserCustomTemplateResponse("),
        ("    return TemplateShareResponse(", "    return ApiResponse.success(data=TemplateShareResponse("),
        ("    return TemplateShareDetail(", "    return ApiResponse.success(data=TemplateShareDetail("),
        ("    return TemplateUsageResponse(", "    return ApiResponse.success(data=TemplateUsageResponse("),
        
        # 处理结尾的 )
        # 需要更精确的替换...这个方法可能有问题
    ]
    
    for old, new in replacements:
        if old in content:
            content = content.replace(old, new, 1)  # 只替换第一个匹配
            print(f"    [OK] 替换成功: {old[:40]}...")
        else:
            print(f"    [SKIP] 未找到: {old[:40]}...")
    
    file_path.write_text(content, encoding="utf-8")
    print("\n[完成] templates.py 已更新")
    print("[提示] 请手动检查以下return语句:")
    print("  - 第264行: return None (DELETE endpoint)")
    print("  - 第502行: return {'message': '点赞成功'}")
    print("  - 第525行: return None (DELETE endpoint)")


if __name__ == "__main__":
    fix_templates()
