"""
修复所有 return 语句，包装为 ApiResponse.success()
"""
from pathlib import Path


def fix_returns_in_file(file_path: Path):
    """修复文件中的所有 return 语句"""
    content = file_path.read_text(encoding="utf-8")
    original_content = content
    
    # 找到所有函数定义及其返回语句
    # 使用更精确的方法：找到每个 async def 到下一个 def 之间的内容
    
    lines = content.split('\n')
    new_lines = []
    in_endpoint = False
    indent_level = 0
    
    for i, line in enumerate(lines):
        # 检测是否是路由端点函数
        if '@router.' in line or (in_endpoint and line.strip().startswith('async def ')):
            in_endpoint = True
        
        # 如果是端点函数的定义行，记录缩进
        if in_endpoint and line.strip().startswith('async def '):
            indent_level = len(line) - len(line.lstrip())
        
        # 检测函数结束（下一个同级或外层函数开始）
        if in_endpoint and line.strip() and not line.strip().startswith('#'):
            current_indent = len(line) - len(line.lstrip())
            if current_indent <= indent_level and i > 0 and 'async def ' in line:
                in_endpoint = False
        
        # 处理 return 语句
        if in_endpoint and line.strip().startswith('return ') and 'ApiResponse' not in line:
            # 提取缩进和返回值
            stripped = line.strip()
            indent = line[:len(line) - len(stripped)]
            
            # 跳过已经是 ApiResponse 的
            if 'ApiResponse.success' in stripped or 'ApiResponse.error' in stripped:
                new_lines.append(line)
                continue
            
            # 提取 return 后面的内容
            return_value = stripped[7:]  # 去掉 'return '
            
            # 如果是多行返回（以 [ 或 { 或对象名开始但没有结束），需要找到完整的返回语句
            if return_value.strip() and (
                (return_value.strip().endswith('[') or 
                 return_value.strip().endswith('(') or
                 (return_value.strip().endswith(',') == False and 
                  not return_value.strip().endswith(')') and 
                  not return_value.strip().endswith(']') and 
                  not return_value.strip().endswith('}') and
                  i + 1 < len(lines) and 
                  lines[i + 1].strip() and 
                  not lines[i + 1].strip().startswith('return') and
                  not lines[i + 1].strip().startswith('#')))
            ):
                # 多行返回，暂时跳过，先标记
                new_lines.append(f"{indent}# TODO: wrap with ApiResponse.success(data=...)")
                new_lines.append(line)
                continue
            
            # 单行返回，直接包装
            # 如果返回值是字典字面量，需要特殊处理
            if return_value.strip().startswith('{'):
                new_lines.append(f"{indent}return ApiResponse.success(data={return_value})")
            else:
                new_lines.append(f"{indent}return ApiResponse.success(data={return_value})")
        else:
            new_lines.append(line)
    
    new_content = '\n'.join(new_lines)
    
    if new_content != original_content:
        file_path.write_text(new_content, encoding="utf-8")
        return True
    return False


def fix_file_manually(file_path: Path, replacements: list):
    """手动指定替换规则来修复文件"""
    content = file_path.read_text(encoding="utf-8")
    
    for old, new in replacements:
        if old in content:
            content = content.replace(old, new)
            print("    [OK] 替换成功")
        else:
            print(f"    [SKIP] 未找到: {old[:50]}...")
    
    file_path.write_text(content, encoding="utf-8")


def main():
    print("=" * 70)
    print("修复所有 return 语句...")
    print("=" * 70)
    
    # ===== completions.py =====
    print("\n[1/4] 修复 completions.py")
    file_path = Path("app/api/v1/completions.py")
    replacements = [
        (
            "    return ReminderCompletionResponse(\n        id=completion.id,",
            "    return ApiResponse.success(data=ReminderCompletionResponse(\n        id=completion.id,"
        ),
        (
            "            completion_time=c.completion_time\n        )\n    ]",
            "            completion_time=c.completion_time\n        )\n    ])"
        ),
        (
            "    return [\n        ReminderCompletionResponse(",
            "    return ApiResponse.success(data=[\n        ReminderCompletionResponse("
        ),
        (
            "            completion_time=c.completion_time\n        )\n        for c in completions\n    ]",
            "            completion_time=c.completion_time\n        )\n        for c in completions\n    ])"
        ),
        (
            "    return ReminderStats(\n        reminder_id=reminder.id,",
            "    return ApiResponse.success(data=ReminderStats(\n        reminder_id=reminder.id,"
        ),
        (
            "        last_completion_time=last_completion.completion_time if last_completion else None\n    )",
            "        last_completion_time=last_completion.completion_time if last_completion else None\n    ))"
        ),
        (
            "    return UserStats(\n        user_id=current_user.id,",
            "    return ApiResponse.success(data=UserStats(\n        user_id=current_user.id,"
        ),
        (
            "        total_completions=total_completions\n    )",
            "        total_completions=total_completions\n    ))"
        ),
    ]
    fix_file_manually(file_path, replacements)
    
    # ===== debug.py =====
    print("\n[2/4] 修复 debug.py")
    file_path = Path("app/api/v1/debug.py")
    replacements = [
        (
            '    return {\n        "status": "healthy",',
            '    return ApiResponse.success(data={\n        "status": "healthy",'
        ),
        (
            '        "version": settings.APP_VERSION\n    }',
            '        "version": settings.APP_VERSION\n    })'
        ),
        (
            '    return {\n        "status": all_healthy,',
            '    return ApiResponse.success(data={\n        "status": all_healthy,'
        ),
        (
            '        "checks": checks\n    }',
            '        "checks": checks\n    })'
        ),
    ]
    fix_file_manually(file_path, replacements)
    
    # ===== push_tasks.py =====
    print("\n[3/4] 修复 push_tasks.py")
    file_path = Path("app/api/v1/push_tasks.py")
    content = file_path.read_text(encoding="utf-8")
    
    # 找到所有需要修复的 return 语句并手动替换
    # GET / - list_push_tasks
    content = content.replace(
        '    return {\n        "tasks": tasks,\n        "total": total,\n        "skip": skip,\n        "limit": limit\n    }',
        '    return ApiResponse.success(data={\n        "tasks": tasks,\n        "total": total,\n        "skip": skip,\n        "limit": limit\n    })'
    )
    
    # GET /{task_id}
    content = content.replace(
        '    return task',
        '    return ApiResponse.success(data=task)'
    )
    
    # POST /
    # PUT /{task_id}  
    # POST /{task_id}/retry
    # 这些可能已经有 return task，需要更精确匹配
    
    # GET /stats/summary
    content = content.replace(
        '    return {\n        "total": total,\n        "pending": pending,\n        "completed": completed,\n        "failed": failed\n    }',
        '    return ApiResponse.success(data={\n        "total": total,\n        "pending": pending,\n        "completed": completed,\n        "failed": failed\n    })'
    )
    
    file_path.write_text(content, encoding="utf-8")
    print("    [OK] 已更新")
    
    # ===== templates.py =====
    print("\n[4/4] 修复 templates.py")
    print("    [INFO] templates.py 的 return 语句较多，需要逐个检查...")
    # 这个文件太复杂，需要单独处理
    
    print("\n" + "=" * 70)
    print("部分文件已修复！templates.py 需要手动检查")
    print("=" * 70)


if __name__ == "__main__":
    main()
