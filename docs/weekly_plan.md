# 本周开发计划 (2025年11月12日-11月18日)

## 🎯 本周目标：完成核心业务闭环

**核心问题：** 当前提醒创建后无法确认完成，无法形成业务闭环。

**本周重点：** 实现 提醒完成确认 → 周期计算 → 推送调度 的完整流程。

---

## 📋 任务清单

### ✅ Day 1-2: 提醒完成确认功能 (P0)

**业务价值：** 形成核心闭环，用户可以完成提醒

#### Task 1.1: 完成确认API
- [ ] `POST /api/v1/reminders/{id}/complete` - 标记完成
  - 更新 `reminders.is_completed = True`
  - 设置 `reminders.completed_at = now()`
  - 记录到 `reminder_completions` 表
  - 触发下次周期计算
  - 创建新的 PushTask

#### Task 1.2: 取消完成API
- [ ] `POST /api/v1/reminders/{id}/uncomplete` - 取消完成
  - 更新 `reminders.is_completed = False`
  - 清空 `reminders.completed_at`
  - 删除对应的 completion 记录

#### Task 1.3: 完成记录查询
- [ ] `GET /api/v1/reminders/{id}/completions` - 历史完成记录
  - 返回该提醒的所有完成记录
  - 支持分页
  - 显示完成人（家庭共享场景用）

#### 实现细节

```python
# app/api/v1/reminders.py

@router.post("/{reminder_id}/complete", response_model=ReminderResponse)
async def complete_reminder(
    reminder_id: int,
    current_user: User = Depends(get_current_active_user),
    reminder_repo: ReminderRepository = Depends(get_reminder_repository),
    db: Session = Depends(get_db)
):
    """标记提醒完成"""
    reminder = reminder_repo.get_by_id(reminder_id, current_user.id)
    if not reminder:
        raise HTTPException(404, "提醒不存在")
    
    # 1. 标记完成
    reminder = reminder_repo.mark_completed(reminder)
    
    # 2. 记录完成记录
    from app.models.reminder_completion import ReminderCompletion
    completion = ReminderCompletion(
        reminder_id=reminder.id,
        user_id=current_user.id,
        completed_at=datetime.now()
    )
    db.add(completion)
    
    # 3. 计算下次提醒时间
    from app.core.recurrence import calculate_next_occurrence
    next_time = calculate_next_occurrence(
        reminder.next_remind_time,
        reminder.recurrence_type,
        reminder.recurrence_config
    )
    reminder.next_remind_time = next_time
    reminder.is_completed = False  # 重置为未完成
    
    # 4. 创建新的推送任务
    from app.services.push_task_service import create_push_task_for_reminder
    create_push_task_for_reminder(db, reminder)
    
    db.commit()
    db.refresh(reminder)
    
    return reminder
```

#### 测试用例

```python
def test_complete_reminder():
    # 1. 创建提醒
    # 2. 标记完成
    # 3. 验证 is_completed = True
    # 4. 验证 completed_at 已设置
    # 5. 验证 completion 记录已创建
    # 6. 验证下次提醒时间已更新
    # 7. 验证新PushTask已创建
```

---

### ✅ Day 3-4: 推送任务调度器 (P0)

**业务价值：** 定时扫描并执行推送任务

#### Task 2.1: 安装和配置APScheduler

```bash
pip install apscheduler
```

```python
# app/core/scheduler.py

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime

scheduler = AsyncIOScheduler()

async def scan_and_push_tasks():
    """每分钟扫描待推送任务"""
    from app.core.database import SessionLocal
    from app.models.push_task import PushTask, PushStatus
    from sqlalchemy import and_
    
    db = SessionLocal()
    try:
        # 查询待推送任务
        tasks = db.query(PushTask).filter(
            and_(
                PushTask.status == PushStatus.PENDING,
                PushTask.scheduled_time <= datetime.now()
            )
        ).limit(100).all()  # 每次最多处理100条
        
        for task in tasks:
            await execute_push_task(task, db)
    finally:
        db.close()

def start_scheduler():
    """启动调度器"""
    scheduler.add_job(
        scan_and_push_tasks,
        trigger=IntervalTrigger(minutes=1),
        id='scan_push_tasks',
        name='扫描并推送任务',
        replace_existing=True
    )
    scheduler.start()
```

#### Task 2.2: 推送执行器（模拟版）

```python
# app/services/push_executor.py

async def execute_push_task(task: PushTask, db: Session):
    """执行推送任务（模拟版）"""
    from app.models.push_log import PushLog
    
    try:
        # 模拟推送
        print(f"[PUSH] 推送任务 {task.id}: {task.title}")
        
        # 模拟成功（90%概率）
        import random
        if random.random() < 0.9:
            task.status = PushStatus.SENT
            task.sent_time = datetime.now()
            task.executed_at = datetime.now()
            
            # 记录日志
            log = PushLog(
                push_task_id=task.id,
                user_id=task.user_id,
                channel='app',
                status='success',
                response_data={'message': '推送成功（模拟）'}
            )
        else:
            # 模拟失败
            task.retry_count += 1
            if task.retry_count >= task.max_retries:
                task.status = PushStatus.FAILED
            task.error_message = "推送失败（模拟）"
            
            log = PushLog(
                push_task_id=task.id,
                user_id=task.user_id,
                channel='app',
                status='failed',
                error_message=task.error_message
            )
        
        db.add(log)
        db.commit()
        
    except Exception as e:
        print(f"[ERROR] 推送失败: {e}")
        task.retry_count += 1
        if task.retry_count >= task.max_retries:
            task.status = PushStatus.FAILED
        task.error_message = str(e)
        db.commit()
```

#### Task 2.3: 集成到主应用

```python
# main.py

from app.core.scheduler import start_scheduler

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化"""
    print("Starting scheduler...")
    start_scheduler()
    print("Scheduler started!")

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理"""
    from app.core.scheduler import scheduler
    scheduler.shutdown()
```

---

### ✅ Day 5: 周期计算引擎增强 (P1)

**业务价值：** 准确计算复杂周期

#### Task 3.1: 修复月度计算

```python
# app/core/recurrence.py (增强版)

from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta

def calculate_next_occurrence(
    current_time: datetime,
    recurrence_type: RecurrenceType,
    recurrence_config: dict
) -> datetime:
    """计算下一次提醒时间（增强版）"""
    
    if recurrence_type == RecurrenceType.MONTHLY:
        interval = recurrence_config.get("interval", 1)
        
        # 使用 relativedelta 处理月末
        next_time = current_time + relativedelta(months=interval)
        
        # 处理工作日调整
        if recurrence_config.get("workday_adjust", False):
            # 如果是周末，顺延到周一
            if next_time.weekday() >= 5:  # 5=Saturday, 6=Sunday
                days_to_add = 7 - next_time.weekday()
                next_time = next_time + timedelta(days=days_to_add)
        
        return next_time
    
    # ... 其他周期类型
```

#### Task 3.2: 单元测试

```python
# tests/test_recurrence.py

def test_monthly_end_of_month():
    """测试月末日期计算"""
    # 1月31日 -> 2月28日
    current = datetime(2025, 1, 31)
    next_time = calculate_next_occurrence(
        current, RecurrenceType.MONTHLY, {"interval": 1}
    )
    assert next_time.day == 28  # 2月只有28天
    assert next_time.month == 2

def test_workday_adjustment():
    """测试工作日调整"""
    # 周六 -> 周一
    current = datetime(2025, 11, 15)  # 周六
    next_time = calculate_next_occurrence(
        current, RecurrenceType.MONTHLY, 
        {"interval": 1, "workday_adjust": True}
    )
    assert next_time.weekday() == 0  # 周一
```

---

### ✅ Day 6-7: 测试和文档 (P1)

#### Task 4.1: 集成测试

```python
# tests/test_complete_flow_v2.py

def test_complete_lifecycle():
    """测试完整生命周期：创建->推送->完成->下次周期"""
    # 1. 创建提醒
    # 2. 验证PushTask生成
    # 3. 模拟调度器执行推送
    # 4. 标记完成
    # 5. 验证下次提醒时间更新
    # 6. 验证新PushTask生成
```

#### Task 4.2: API文档更新

- 使用 FastAPI 自动生成的 OpenAPI 文档
- 访问 `http://localhost:8000/docs`
- 添加详细的接口说明和示例

---

## 📊 验收标准

### 功能验收
- [ ] 用户可以标记提醒完成
- [ ] 完成后自动计算下次提醒时间
- [ ] 调度器每分钟自动扫描任务
- [ ] 推送任务可以执行（模拟）
- [ ] 推送日志正确记录
- [ ] 月末日期计算准确
- [ ] 工作日调整正常工作

### 代码质量
- [ ] 所有新增代码有单元测试
- [ ] 测试覆盖率 > 80%
- [ ] 代码通过 pylint 检查
- [ ] API文档完整

### 性能要求
- [ ] 调度器不阻塞主应用
- [ ] 每分钟可处理100+任务
- [ ] 数据库查询有索引优化

---

## 🚀 下周预告 (11月19日-11月25日)

1. **系统模板库** - 预置20个常用模板
2. **基础统计API** - 完成率、分类分布
3. **家庭共享功能** - 开始核心API开发

---

**负责人：** AI Agent  
**更新时间：** 2025-11-12  
**状态：** 🟢 Ready to Start
