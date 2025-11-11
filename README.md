# TimeKeeper - 周期提醒 APP 后端

## 📋 项目简介

TimeKeeper 是一个专注于周期提醒的应用后端服务,帮助用户管理生活中的重要事件。

### 核心特点

- 🔄 **智能周期管理**: 支持日/周/月/年等多种周期类型
- 🎯 **场景模板**: 6大预设模板(居住/健康/宠物/财务/证件/纪念)
- 🔔 **多渠道提醒**: APP推送、短信、微信、语音电话
- 🎤 **语音输入**(规划中): 语音识别 + AI 智能解析
- 👨‍👩‍👧 **家庭共享**(规划中): 多成员提醒共享

## 🏗️ 技术栈

- **后端框架**: FastAPI
- **数据库**: PostgreSQL + Redis
- **ORM**: SQLAlchemy
- **数据库迁移**: Alembic
- **认证**: JWT (python-jose)
- **包管理**: uv

## 📁 项目结构

```
TimeKeeper/
├── app/                          # 应用主目录
│   ├── api/                      # API 路由
│   │   └── v1/                   # API v1 版本
│   │       ├── users.py          # 用户相关 API
│   │       └── reminders.py      # 提醒相关 API
│   ├── core/                     # 核心配置
│   │   ├── config.py             # 应用配置
│   │   ├── database.py           # 数据库连接
│   │   └── security.py           # 安全工具(JWT, 密码哈希)
│   ├── models/                   # 数据模型
│   │   ├── user.py               # 用户模型
│   │   ├── reminder.py           # 提醒模型
│   │   └── push_task.py          # 推送任务模型
│   ├── schemas/                  # Pydantic 模型
│   │   ├── user.py               # 用户 Schema
│   │   └── reminder.py           # 提醒 Schema
│   └── services/                 # 业务逻辑服务
│       └── recurrence_engine.py  # 周期计算引擎
├── alembic/                      # 数据库迁移文件
├── tests/                        # 测试文件
├── main.py                       # 应用入口
├── pyproject.toml                # 项目配置和依赖
├── alembic.ini                   # Alembic 配置
├── .env.example                  # 环境变量示例
└── README.md                     # 项目文档
```

## 🚀 快速开始

### 前置要求

- Python 3.12+
- PostgreSQL 13+
- Redis 6+ (可选)
- uv (Python 包管理工具)

### 安装步骤

1. **克隆项目**

```bash
git clone <repository-url>
cd TimeKeeper
```

2. **安装 uv**

```bash
pip install uv
```

3. **创建虚拟环境并安装依赖**

```bash
# uv 会自动创建虚拟环境并安装依赖
uv sync
```

4. **配置环境变量**

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件,配置数据库连接等信息
# 至少需要配置:
# - DATABASE_URL: PostgreSQL 连接字符串
# - SECRET_KEY: JWT 密钥(生产环境务必修改)
```

5. **初始化数据库**

```bash
# 激活虚拟环境 (Windows)
.venv\Scripts\activate

# 创建数据库迁移
alembic revision --autogenerate -m "Initial migration"

# 执行迁移
alembic upgrade head
```

6. **启动服务**

```bash
# 开发模式(热重载)
python main.py

# 或使用 uvicorn
uvicorn main:app --reload
```

7. **访问 API 文档**

打开浏览器访问:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🔧 开发指南

### 数据库迁移

```bash
# 创建新迁移
alembic revision --autogenerate -m "描述迁移内容"

# 执行迁移(升级)
alembic upgrade head

# 回滚迁移(降级)
alembic downgrade -1

# 查看迁移历史
alembic history
```

### 添加新依赖

```bash
# 使用 uv 添加依赖
uv add package-name

# 添加开发依赖
uv add --dev pytest
```

### 代码规范

- 遵循 PEP 8 代码风格
- 使用 4 空格缩进
- 方法不超过 20-30 行
- 重要功能需要添加注释

### API 端点

#### 用户相关
- `POST /api/v1/users/register` - 用户注册
- `POST /api/v1/users/login` - 用户登录
- `GET /api/v1/users/me` - 获取当前用户信息
- `PUT /api/v1/users/me` - 更新用户信息

#### 提醒相关
- `POST /api/v1/reminders/` - 创建提醒
- `GET /api/v1/reminders/` - 获取提醒列表
- `GET /api/v1/reminders/{id}` - 获取提醒详情
- `PUT /api/v1/reminders/{id}` - 更新提醒
- `DELETE /api/v1/reminders/{id}` - 删除提醒

## 📊 数据模型

### 用户表 (users)
- id: 用户ID
- phone: 手机号(唯一)
- hashed_password: 密码哈希
- nickname: 昵称
- settings: 用户设置(JSON)

### 提醒表 (reminders) - 核心表
- id: 提醒ID
- user_id: 用户ID(外键)
- title: 提醒标题
- category: 分类(rent/health/pet/finance/document/memorial)
- recurrence_type: 周期类型(daily/weekly/monthly/yearly)
- recurrence_config: 周期配置(JSON)
- next_remind_time: 下次提醒时间
- remind_channels: 提醒渠道(JSON)
- is_active: 是否启用

### 推送任务表 (push_tasks)
- id: 任务ID
- reminder_id: 关联提醒ID
- user_id: 用户ID
- scheduled_time: 计划推送时间
- status: 状态(pending/sent/failed)

## 🎯 开发路线图

### MVP 版本 (v0.1.0) - ✅ 当前
- [x] 项目框架搭建
- [x] 用户注册登录 API
- [x] 提醒 CRUD API
- [x] 数据库模型设计
- [x] 周期计算引擎基础版
- [ ] JWT 认证中间件完善
- [ ] APP 推送集成
- [ ] 单元测试

### v0.2.0 - 规划中
- [ ] 语音识别集成
- [ ] AI 智能解析(DeepSeek API)
- [ ] 短信推送功能
- [ ] 推送任务调度系统

### v0.3.0 - 未来
- [ ] 家庭共享功能
- [ ] 数据统计分析
- [ ] 性能优化
- [ ] 压力测试

## 📝 环境变量说明

| 变量名 | 说明 | 示例值 |
|--------|------|--------|
| DATABASE_URL | PostgreSQL 连接字符串 | postgresql://user:pass@localhost:5432/timekeeper |
| REDIS_URL | Redis 连接字符串 | redis://localhost:6379/0 |
| SECRET_KEY | JWT 密钥(至少32字符) | your-secret-key-change-in-production |
| DEBUG | 调试模式 | True/False |

## 🤝 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证。

---

**打造最简单、最好用的周期提醒工具!** 🎉
