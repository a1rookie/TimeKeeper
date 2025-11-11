# TimeKeeper 开发快速指南

## 立即开始

### 1. 首次启动配置

```bash
# 1. 复制环境配置文件
copy .env.example .env

# 2. 编辑 .env 文件，至少修改以下配置：
# - DATABASE_URL: 你的 PostgreSQL 数据库连接字符串
# - SECRET_KEY: 随机生成一个至少32位的密钥

# 3. 激活虚拟环境
.venv\Scripts\activate

# 4. 创建数据库（需要先创建 PostgreSQL 数据库）
# 在 PostgreSQL 中执行: CREATE DATABASE timekeeper;

# 5. 运行数据库迁移
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

### 2. 日常开发

```bash
# 激活虚拟环境
.venv\Scripts\activate

# 启动开发服务器（自动重载）
python main.py
# 或
uvicorn main:app --reload

# 访问 API 文档
# http://localhost:8000/docs
```

### 3. 常用命令

```bash
# 添加新的 Python 包
uv add package-name

# 创建数据库迁移
alembic revision --autogenerate -m "迁移描述"

# 应用迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1

# 运行测试（未来实现）
pytest
```

## 项目核心功能模块

### ✅ 已实现

1. **用户模块** (`app/api/v1/users.py`)
   - 用户注册
   - 用户登录（返回 JWT token）
   - 获取/更新用户信息（TODO: 完善 JWT 认证）

2. **提醒模块** (`app/api/v1/reminders.py`)
   - 创建提醒
   - 查询提醒列表
   - 获取提醒详情
   - 更新提醒
   - 删除提醒

3. **周期计算引擎** (`app/services/recurrence_engine.py`)
   - 每日周期
   - 每周周期
   - 每月周期（支持跳过周末）
   - 每年周期
   - 自定义周期

4. **数据模型**
   - User: 用户表
   - Reminder: 提醒表（核心）
   - PushTask: 推送任务表

### 🔨 待完善

1. **JWT 认证中间件**
   - 需要实现获取当前用户的依赖注入
   - 在 `app/core/security.py` 中添加 `get_current_user` 函数

2. **推送系统**
   - APP 推送集成（个推/极光）
   - 推送任务调度器
   - 多渠道推送支持

3. **高级功能**
   - 语音识别
   - AI 智能解析
   - 场景模板系统
   - 家庭共享

## 快速测试 API

### 1. 用户注册

```bash
curl -X POST "http://localhost:8000/api/v1/users/register" \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "13800138000",
    "password": "password123",
    "nickname": "测试用户"
  }'
```

### 2. 用户登录

```bash
curl -X POST "http://localhost:8000/api/v1/users/login" \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "13800138000",
    "password": "password123"
  }'
```

### 3. 创建提醒

```bash
curl -X POST "http://localhost:8000/api/v1/reminders/" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "交房租",
    "description": "每月25号交房租",
    "category": "rent",
    "recurrence_type": "monthly",
    "recurrence_config": {"day": 25, "skip_weekend": true},
    "first_remind_time": "2025-11-25T09:00:00",
    "remind_channels": ["app", "sms"],
    "advance_minutes": 60
  }'
```

## 下一步工作建议

1. **完善 JWT 认证**
   - 实现 `get_current_user` 依赖
   - 为需要认证的端点添加认证保护

2. **集成推送服务**
   - 注册个推或极光推送账号
   - 实现推送服务封装
   - 创建推送任务调度器

3. **编写测试**
   - 为核心功能编写单元测试
   - API 端点集成测试

4. **优化周期计算**
   - 处理边界情况
   - 添加更多测试案例

## 问题排查

### 导入错误（pydantic_settings, fastapi 等）

这是因为 IDE 没有识别虚拟环境。解决方法：
1. 在 VS Code 中按 `Ctrl+Shift+P`
2. 输入 "Python: Select Interpreter"
3. 选择 `.venv` 中的 Python 解释器

### 数据库连接失败

1. 确保 PostgreSQL 服务正在运行
2. 检查 `.env` 文件中的 `DATABASE_URL` 配置
3. 确保数据库已创建：`CREATE DATABASE timekeeper;`

### Alembic 迁移失败

1. 检查模型导入是否正确
2. 查看 `alembic/env.py` 是否正确配置
3. 尝试删除 `alembic/versions` 中的文件重新生成

## 技术支持

- 查看完整文档：`README.md`
- AI 开发指南：`周期提醒APP - AI开发实施指南.md`
- 开发规范：`developer_notes.md`
- 代理工作模版：`AGENTS.md`
