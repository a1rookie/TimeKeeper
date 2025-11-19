# 周期提醒后端开发规范

# TimeKeeper 项目代码开发规范

## 📋 目录

1. 项目概述
2. 技术栈与架构
3. 代码组织规范
4. 编码规范
5. 数据库规范
6. API 开发规范
7. 日志规范
8. 测试规范
9. 依赖管理
10. Git 协作规范
11. 安全与配置
12. 可靠性规范
13. 可观测性

---

## 1. 项目概述

**项目名称**: TimeKeeper - 周期提醒 APP 后端服务

**技术架构**: FastAPI + SQLAlchemy 2.0 (异步) + PostgreSQL + Redis

**Python 版本**: 3.12+

**包管理器**: uv (快速 Python 包管理器)

### 核心特性

- 全异步架构：asyncio + asyncpg
- SQLAlchemy 2.0：Mapped 类型注解和异步 ORM
- 结构化日志：structlog
- 统一响应格式：ApiResponse[T]
- JWT 认证

---

## 2. 技术栈与架构

### 2.1 核心技术栈

```toml
# 主要依赖 (pyproject.toml)
fastapi >= 0.121.1
sqlalchemy[asyncio] >= 2.0.44
asyncpg >= 0.30.0
alembic >= 1.17.1
structlog >= 25.5.0
redis >= 7.0.1
uvicorn[standard] >= 0.38.0
pydantic-settings >= 2.12.0
python-jose[cryptography] >= 3.5.0
```

### 2.2 项目架构

```
TimeKeeper/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── [users.py](http://users.py)
│   │       ├── [reminders.py](http://reminders.py)
│   │       └── push_[tasks.py](http://tasks.py)
│   ├── core/
│   │   ├── [config.py](http://config.py)
│   │   ├── [database.py](http://database.py)
│   │   ├── [security.py](http://security.py)
│   │   ├── redis_[client.py](http://client.py)
│   │   └── logging_[config.py](http://config.py)
│   ├── models/
│   ├── repositories/
│   ├── schemas/
│   └── services/
├── alembic/
├── tests/
├── scripts/
├── logs/
├── docs/
├── [main.py](http://main.py)
├── pyproject.toml
└── .env
```

---

## 3. 代码组织规范

### 3.1 分层架构原则

```
API 路由层 (api/)
    ↓
Schema 层 (schemas/)
    ↓
Service 层 (services/)
    ↓
Repository 层 (repositories/)
    ↓
Model 层 (models/)
```

### 3.2 文件命名规范

- 模块文件：snake_case
- 类名：PascalCase
- 函数/方法：snake_case
- 常量：UPPER_CASE
- 私有方法：前缀 _

### 3.3 目录结构规则

```python
# app/repositories/__init__.py 示例
from app.repositories.user_repository import UserRepository
from app.repositories.reminder_repository import ReminderRepository
from sqlalchemy.ext.asyncio import AsyncSession

def get_user_repository(db: AsyncSession) -> UserRepository:
    return UserRepository(db)

def get_reminder_repository(db: AsyncSession) -> ReminderRepository:
    return ReminderRepository(db)
```

---

## 4. 编码规范

### 4.1 Python 代码风格

### 4.1.1 导入顺序

```python
"""
模块说明
"""
# 1. 标准库
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

# 2. 第三方库
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

# 3. 本地应用
from app.core.database import get_db
from app.models.user import User
from app.schemas.response import ApiResponse

import structlog
logger = structlog.get_logger(__name__)
```

### 4.1.2 类型注解

- 所有函数/方法必须有类型注解

```python
from sqlalchemy import select

async def get_user_by_id(user_id: int, db: AsyncSession) -> Optional[User]:
    result = await db.execute(select(User).where([User.id](http://User.id) == user_id))
    return result.scalar_one_or_none()
```

### 4.1.3 文档字符串

- 所有公共函数/类必须有文档字符串

```python
def create_reminder(self, user_id: int, title: str) -> "Reminder":
    """创建新提醒。"""
```

### 4.2 异步编程规范

- I/O 操作必须 await
- 纯计算逻辑保持同步函数

```python
async def create_user(db: AsyncSession, phone: str) -> User:
    user = User(phone=phone)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
```

### 4.3 Ruff 代码规范（Lint + Format）

- 统一使用 Ruff 进行“静态检查 + 自动格式化”
- Python 目标版本 py312，行长 100

```toml
[tool.ruff]
line-length = 100
indent-width = 4
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP", "ANN"]
ignore = []

[tool.ruff.lint.isort]
known-first-party = ["app"]
combine-as-imports = true
force-sort-within-sections = true

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
docstring-code-format = true

[tool.ruff.lint.per-file-ignores]
"tests/**/*" = ["ANN", "S101"]
```

常用命令：

```bash
uv add ruff --group dev
uv run ruff check .
uv run ruff format .
uv run ruff check . --fix
```

> 要点：公共 API 强制类型注解；使用现代语法 `list[int]`、`X | None`；导入按“标准库 → 第三方 → 本地”。
> 

### 4.4 类型与容器导入规范（[collections.abc](http://collections.abc) vs typing）

- 容器 ABC 从 [`collections.abc`](http://collections.abc) 导入：`Sequence`、`Iterable`、`Mapping` 等
- 使用内置泛型：`list[int]`、`dict[str, Any]`
- 仅在需要时从 `typing` 导入：`Any`、`Literal`、`TypedDict`、`Annotated`、`Protocol`、`overload`、`cast`

```python
from [collections.abc](http://collections.abc) import Iterable, Mapping, Sequence
from typing import Any, Literal, TypedDict

def head(xs: Sequence[int]) -> int:
    return xs[0]

Users = list[dict[str, Any]]
```

### 4.5 预提交钩子与 CI 门禁

- 本地 pre-commit 执行格式化与静态检查
- CI 门禁：uv sync → ruff format --check → ruff check → 类型检查 → 测试

```yaml
# .pre-commit-config.yaml
repos:
  - repo: [https://github.com/astral-sh/ruff-pre-commit](https://github.com/astral-sh/ruff-pre-commit)
    rev: v0.6.9
    hooks:
      - id: ruff
        args: ["--fix"]
      - id: ruff-format
  - repo: [https://github.com/pre-commit/pre-commit-hooks](https://github.com/pre-commit/pre-commit-hooks)
    rev: v4.6.0
    hooks:
      - id: end-of-file-fixer
      - id: trailing-whitespace
      - id: check-yaml
```

```yaml
# .github/workflows/ci.yml
name: ci
on: [push, pull_request]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uv sync
      - run: uv run ruff format --check .
      - run: uv run ruff check .
      - run: uv run pytest -q
```

### 4.6 类型检查（mypy/pyright）

```toml
# mypy (pyproject.toml)
[tool.mypy]
python_version = "3.12"
strict = true
warn_unused_ignores = true
warn_redundant_casts = true
exclude = ["alembic/", "tests/"]

[mypy-tests.*]
ignore_errors = true
```

```json
// pyrightconfig.json
{
  "$schema": "[https://raw.githubusercontent.com/microsoft/pyright/main/packages/vscode-pyright/schemas/pyrightconfig.schema.json](https://raw.githubusercontent.com/microsoft/pyright/main/packages/vscode-pyright/schemas/pyrightconfig.schema.json)",
  "pythonVersion": "3.12",
  "typeCheckingMode": "strict",
  "exclude": ["alembic", "tests"],
  "venvPath": ".",
  "venv": ".venv"
}
```

---

## 5. 数据库规范

### 5.1 SQLAlchemy 2.0 模型定义

```python
from datetime import datetime
from typing import Optional
from sqlalchemy import String, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    phone: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    nickname: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=[func.now](http://func.now)())
    updated_at: Mapped[datetime] = mapped_column(server_default=[func.now](http://func.now)(), onupdate=[func.now](http://func.now)())
```

### 5.2 Repository 层规范

```python
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User

class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: int) -> Optional[User]:
        result = await self.db.execute(select(User).where([User.id](http://User.id) == user_id))
        return result.scalar_one_or_none()
```

### 5.3 数据库迁移规范（Alembic）

```bash
uv run alembic revision --autogenerate -m "描述性的迁移说明"
uv run alembic upgrade head
uv run alembic downgrade -1 # 回滚
```

---

## 6. API 开发规范

### 6.1 统一响应格式

```python
from app.schemas.response import ApiResponse

@router.get("/me", response_model=ApiResponse[User])
async def get_current_user(current_user: User = Depends(get_current_active_user)):
    return ApiResponse.success(data=current_user)
```

### 6.2 路由定义规范

- 使用 status code、summary、description 明确语义

### 6.3 错误处理规范

- HTTPException 映射标准状态码
- Service 层可返回 ApiResponse.error(code, message)

### 6.4 依赖注入规范

- FastAPI Depends 注入 db、当前用户、仓库实例

### 6.5 错误码与异常映射

- 2xx 成功（统一业务 code=200）
- 4xx 客户端错误：400/401/403/404/409/422
- 5xx 服务端错误：500/503

```python
class DomainError(Exception):
    code: int = 400
    message: str = "业务错误"
```

### 6.6 分页、排序与过滤

- 分页：page 从 1 开始；page_size 默认 20，最大 100
- 返回：items + page + page_size + total
- 排序：sort=field:asc|desc；可多字段
- 过滤：q_xxx 前缀，如 q_created_at_gte

### 6.7 版本管理与弃用策略

- 路由前缀 /v1；破坏性变更才提升主版本
- 弃用：响应头 Deprecation 与 Sunset；文档标注替代方案

---

## 7. 日志规范

- 统一使用 structlog，按级别输出，支持上下文绑定

```python
import structlog
logger = structlog.get_logger(__name__)
logger = logger.bind(request_id=request_id)
[logger.info](http://logger.info)("processing_started")
```

---

## 8. 测试规范

- 目录：tests/test_api, test_repositories, test_services
- 命名：TestClass + test_xxx_yyy
- 常用命令：pytest、pytest -v、pytest -s

---

## 9. 依赖管理

- 使用 uv：uv add / uv sync / uv remove / uv sync --upgrade
- 分组依赖：project.dependencies 与 [dependency-groups.dev](http://dependency-groups.dev)

---

## 10. Git 协作规范

- 分支：main、develop、feature/xxx、bugfix/xxx、refactor/xxx
- 提交消息：遵循 Conventional Commits
- .gitignore：env、logs、__pycache__、IDE、db 文件

---

## 11. 安全与配置

### 11.1 日志与隐私（PII 脱敏）

- 手机号、邮箱、Token、密码哈希等敏感信息严禁入日志
- 字段白名单：request_id, user_id, path, method, status_code, latency_ms
- 字段黑名单：password, authorization, refresh_token, otp_code

### 11.2 配置与密钥管理

- 密钥仅在环境/密管；支持轮换；.env 仅用于本地且忽略提交

### 11.3 认证与会话（JWT）

- 算法优先 RS256/EdDSA；访问 Token 短效，刷新 Token 长效；支持吊销/黑名单

### 11.4 CORS 与速率限制

- CORS 限制来源与方法；按用户与 IP 做速率限制

---

## 12. 可靠性规范

### 12.1 超时、重试与退避

- 外部依赖设置超时；幂等操作使用指数退避与抖动

### 12.2 幂等性与去重

- 写操作要求 Idempotency-Key；服务端短期去重缓存

### 12.3 降级与熔断

- 下游不可用时快速失败；提供降级路径

---

## 13. 可观测性

### 13.1 指标

- 请求量、成功率、P95/P99、错误率、队列积压

### 13.2 追踪

- OpenTelemetry，跨服务传递 Trace Context

### 13.3 健康检查

---

## ✅ 代码审查清单

基础代码与风格

- [ ]  所有函数都有类型注解；公共接口遵循 ANN 规则
- [ ]  所有公共函数/类都有文档字符串，示例简明
- [ ]  导入分组与排序：标准库 → 第三方 → 本地，isort 规则通过
- [ ]  Ruff 通过：`ruff format --check` 与 `ruff check` 均为 0 问题

异步与数据访问

- [ ]  I/O 必须使用 `async`/`await`，纯计算保持同步
- [ ]  数据库访问经 Repository 层，事务与 `commit/refresh` 使用正确
- [ ]  Alembic 迁移文件已生成且可升级回滚

API 契约与错误处理

- [ ]  API 响应统一使用 `ApiResponse[T]`
- [ ]  错误码与异常映射符合规范（400/401/403/404/409/422/500/503）
- [ ]  分页/排序/过滤参数与返回结构符合约定
- [ ]  版本与弃用策略：必要时添加 `Deprecation` 与 `Sunset` 响应头

质量门禁与工具链

- [ ]  pre-commit 本地通过（ruff、格式、YAML 等）
- [ ]  CI 流程通过：uv sync → ruff format --check → ruff check → 类型检查 → 测试
- [ ]  类型检查通过（mypy 或 pyright 严格模式）
- [ ]  测试通过（pytest），关键路径具备测试覆盖

安全与配置

- [ ]  日志脱敏：PII 不落盘，黑白名单生效
- [ ]  秘钥与配置不入库，.env 未提交，具备轮换策略
- [ ]  JWT 策略：算法、有效期、刷新与吊销逻辑到位
- [ ]  CORS 与速率限制正确配置

可靠性与可观测性

- [ ]  外部依赖设置超时，幂等操作具备指数退避与抖动
- [ ]  写操作具备幂等键与去重策略
- [ ]  关键路径具备降级与熔断策略
- [ ]  指标（QPS、成功率、P95/P99、错误率）与 Tracing 上报
- [ ]  健康检查：Liveness 与 Readiness 探针可用

协作与提交

- [ ]  提交消息符合 Conventional Commits 规范
- [ ]  新增依赖使用 `uv add` 并已同步锁文件
- [ ]  .gitignore 覆盖环境、日志、缓存、IDE、数据库文件