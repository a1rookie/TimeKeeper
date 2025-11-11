# Repository Layer - 数据访问层

## 概述

Repository层负责封装所有数据库操作，使用SQLAlchemy 2.0的现代语法。

## 架构特点

### ✅ SQLAlchemy 2.0语法
- 使用 `select()` 替代 `query()`
- 使用 `execute()` + `scalars()` 获取结果
- 显式事务管理
- 类型安全的查询构建

### ✅ 关注点分离
- **API层** (`app/api/v1/`): 处理HTTP请求/响应，验证权限
- **Service层** (`app/services/`): 业务逻辑，事务编排
- **Repository层** (`app/repositories/`): 数据访问，CRUD操作
- **Model层** (`app/models/`): ORM模型定义

## 文件结构

```
app/repositories/
├── __init__.py              # 导出所有Repository
├── push_task_repository.py  # 推送任务数据访问
├── reminder_repository.py   # 提醒数据访问
└── user_repository.py       # 用户数据访问
```

## 使用示例

### 基本查询

```python
from sqlalchemy.orm import Session
from app.repositories.push_task_repository import PushTaskRepository

def get_user_tasks(db: Session, user_id: int):
    # 使用Repository代替直接查询
    tasks, total = PushTaskRepository.list_by_user(
        db=db,
        user_id=user_id,
        skip=0,
        limit=20
    )
    return tasks
```

### 创建记录

```python
from app.repositories.push_task_repository import PushTaskRepository

def create_task(db: Session, user_id: int, reminder_id: int):
    task = PushTaskRepository.create(
        db=db,
        user_id=user_id,
        reminder_id=reminder_id,
        title="Test Task",
        content="Test content",
        channels=["app"],
        scheduled_time=datetime.now()
    )
    return task
```

### 更新记录

```python
from app.repositories.push_task_repository import PushTaskRepository

def update_task_time(db: Session, task_id: int, user_id: int):
    # 1. 获取任务
    task = PushTaskRepository.get_by_id(db, task_id, user_id)
    
    if not task:
        raise ValueError("Task not found")
    
    # 2. 更新
    updated_task = PushTaskRepository.update(
        db=db,
        task=task,
        scheduled_time=datetime.now() + timedelta(hours=1)
    )
    
    return updated_task
```

### 复杂查询

```python
from app.repositories.push_task_repository import PushTaskRepository
from app.models.push_task import PushStatus

def get_pending_tasks(db: Session, user_id: int):
    tasks, total = PushTaskRepository.list_by_user(
        db=db,
        user_id=user_id,
        status=PushStatus.PENDING,  # 筛选条件
        skip=0,
        limit=100
    )
    return tasks
```

## SQLAlchemy 2.0 语法对比

### 旧语法 (1.x)
```python
# ❌ 不推荐
tasks = db.query(PushTask).filter(
    PushTask.user_id == user_id,
    PushTask.status == PushStatus.PENDING
).all()
```

### 新语法 (2.0)
```python
# ✅ 推荐
from sqlalchemy import select, and_

stmt = select(PushTask).where(
    and_(
        PushTask.user_id == user_id,
        PushTask.status == PushStatus.PENDING
    )
)
result = db.execute(stmt)
tasks = result.scalars().all()
```

## Repository方法命名规范

- `get_by_id()` - 根据ID获取单条记录
- `get_by_xxx()` - 根据特定字段获取
- `list_by_user()` - 获取用户的列表（带分页）
- `create()` - 创建新记录
- `update()` - 更新记录
- `delete()` / `cancel()` - 删除/取消记录
- `mark_as_xxx()` - 标记状态
- `get_statistics()` - 获取统计信息

## 事务管理

Repository不负责事务管理，事务由调用方（Service或API）控制：

```python
# Service层负责事务
def create_reminder_with_task(db: Session, user_id: int, data: dict):
    try:
        # 创建提醒
        reminder = ReminderRepository.create(db, ...)
        
        # 创建推送任务
        task = PushTaskRepository.create(db, ...)
        
        # 统一提交
        db.commit()
        
        return reminder, task
    except Exception as e:
        db.rollback()
        raise
```

## 测试

Repository层应该有独立的单元测试：

```python
def test_create_push_task(db_session):
    task = PushTaskRepository.create(
        db=db_session,
        user_id=1,
        reminder_id=1,
        title="Test",
        content="Test content",
        channels=["app"],
        scheduled_time=datetime.now()
    )
    
    assert task.id is not None
    assert task.status == PushStatus.PENDING
```

## 优势

1. **可维护性**: 数据访问逻辑集中管理
2. **可测试性**: 易于mock和单元测试
3. **可复用性**: 同一查询可在多处使用
4. **类型安全**: 使用SQLAlchemy 2.0的类型提示
5. **性能优化**: 统一处理查询优化和缓存

## 注意事项

1. **不要在Repository中调用其他Repository**
2. **保持Repository方法的原子性**（单一职责）
3. **复杂业务逻辑放在Service层**
4. **Repository只返回模型对象，不返回Pydantic schema**
5. **使用类型提示提高代码可读性**
