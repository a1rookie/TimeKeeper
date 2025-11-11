# TimeKeeper 开发大纲

> **版本**: v1.0  
> **更新日期**: 2025-11-10  
> **预计总工期**: 6-10 周

---

## 📋 开发阶段总览

| 阶段 | 内容 | 优先级 | 预计工期 | 状态 |
|------|------|--------|----------|------|
| **阶段1** | 核心功能完善 | 🔴 最高 | 1-2周 | 📋 待开始 |
| **阶段2** | 推送系统 | 🔴 最高 | 1-2周 | 📋 待开始 |
| **阶段3** | 场景模板系统 | 🟡 中等 | 1周 | 📋 待开始 |
| **阶段4** | 高级功能 | 🟢 较低 | 2-3周 | 📋 待开始 |
| **阶段5** | 测试和优化 | 🔴 最高 | 1-2周 | 📋 待开始 |

---

## 🎯 阶段 1: 核心功能完善 (1-2周)

> **目标**: 完善基础认证和数据库，确保核心功能可用

### 1.1 完善 JWT 认证中间件 ⭐⭐⭐

**任务清单**:
- [ ] 实现 `get_current_user` 依赖注入函数
- [ ] 创建 `get_current_active_user` 依赖
- [ ] 处理 token 过期和无效情况
- [ ] 为需要认证的 API 端点添加依赖

**文件涉及**:
- `app/core/security.py` - 添加认证依赖
- `app/api/v1/users.py` - 保护用户信息端点
- `app/api/v1/reminders.py` - 保护提醒管理端点

**验收标准**:
- ✅ 未登录用户无法访问受保护端点
- ✅ Token 过期返回 401 错误
- ✅ 每个请求能正确识别当前用户

---

### 1.2 数据库初始化和测试 ⭐⭐⭐

**任务清单**:
- [ ] 创建 `.env` 文件并配置数据库连接
- [ ] 在 PostgreSQL 中创建数据库
- [ ] 运行 Alembic 迁移生成初始表结构
- [ ] 测试数据库连接和基本 CRUD 操作
- [ ] 创建数据库初始化脚本 (seed data)

**命令清单**:
```bash
# 1. 创建数据库
psql -U postgres -c "CREATE DATABASE timekeeper;"

# 2. 生成迁移
alembic revision --autogenerate -m "Initial tables"

# 3. 执行迁移
alembic upgrade head

# 4. 验证表结构
psql -U postgres -d timekeeper -c "\dt"
```

**验收标准**:
- ✅ 三个核心表创建成功 (users, reminders, push_tasks)
- ✅ 外键关系正确
- ✅ 索引创建正确
- ✅ 可以执行 upgrade 和 downgrade

---

### 1.3 完善周期计算引擎 ⭐⭐

**任务清单**:
- [ ] 处理闰年边界情况 (2月29日)
- [ ] 处理月末边界情况 (30/31日)
- [ ] 处理跨年周期计算
- [ ] 添加时区支持
- [ ] 编写单元测试覆盖所有边界情况

**测试用例**:
- 闰年 2月29日 → 非闰年 2月28日
- 月末日期 (1月31日 → 2月28日)
- 跨年计算 (12月31日 → 1月1日)
- 每周提醒跨周计算
- 跳过周末逻辑

**文件涉及**:
- `app/services/recurrence_engine.py` - 完善计算逻辑
- `tests/test_recurrence_engine.py` - 单元测试 (新建)

**验收标准**:
- ✅ 所有边界情况测试通过
- ✅ 测试覆盖率 > 90%
- ✅ 性能测试: 1000次计算 < 100ms

---

### 1.4 API 端到端测试 ⭐⭐⭐

**任务清单**:
- [ ] 使用 Postman/curl 测试用户注册登录
- [ ] 测试提醒完整 CRUD 流程
- [ ] 测试错误处理 (404, 401, 400)
- [ ] 测试分页和筛选功能
- [ ] 编写 API 测试脚本

**测试场景**:
1. 用户注册 → 登录 → 获取 token
2. 使用 token 创建提醒
3. 查询提醒列表 (分页、筛选)
4. 更新提醒 (修改周期配置)
5. 删除提醒
6. 测试无效 token 访问

**文件涉及**:
- `tests/test_api_users.py` - 用户 API 测试 (新建)
- `tests/test_api_reminders.py` - 提醒 API 测试 (新建)
- `scripts/test_api.sh` - API 测试脚本 (新建)

**验收标准**:
- ✅ 完整流程测试通过
- ✅ 所有错误情况正确处理
- ✅ API 响应时间 < 200ms (简单查询)

---

## 🔔 阶段 2: 推送系统 (1-2周)

> **目标**: 实现多渠道推送和任务调度

### 2.1 推送服务封装 ⭐⭐⭐

**任务清单**:
- [ ] 选择推送服务商 (个推/极光/Firebase)
- [ ] 注册账号并获取 API 密钥
- [ ] 封装 APP 推送接口
- [ ] 实现推送结果回调处理
- [ ] 添加推送日志记录

**文件涉及**:
- `app/services/push_service.py` - 推送服务封装 (新建)
- `app/core/config.py` - 添加推送服务配置

**接口设计**:
```python
class PushService:
    async def send_app_push(user_id, title, content) -> PushResult
    async def send_sms(phone, content) -> PushResult
    async def send_wechat(user_id, content) -> PushResult  # 未来
```

**验收标准**:
- ✅ APP 推送成功发送
- ✅ 推送失败正确记录
- ✅ 支持批量推送

---

### 2.2 推送任务调度器 ⭐⭐⭐

**任务清单**:
- [ ] 使用 APScheduler 创建定时任务
- [ ] 实现每分钟扫描待推送任务
- [ ] 根据提醒创建推送任务
- [ ] 实现失败重试机制 (最多3次)
- [ ] 推送成功后更新提醒的 next_remind_time

**文件涉及**:
- `app/services/push_scheduler.py` - 任务调度器 (新建)
- `app/services/reminder_service.py` - 提醒业务逻辑 (新建)
- `main.py` - 启动调度器

**核心逻辑**:
1. 每分钟扫描 `next_remind_time <= now` 的提醒
2. 为每个提醒创建 `PushTask`
3. 发送推送
4. 更新提醒的 `next_remind_time` (调用周期引擎)
5. 记录推送结果

**验收标准**:
- ✅ 调度器稳定运行 24 小时无崩溃
- ✅ 推送准点率 > 95% (误差 < 1分钟)
- ✅ 失败任务自动重试

---

### 2.3 推送任务管理 API ⭐⭐

**任务清单**:
- [ ] 查询推送历史 API
- [ ] 推送任务详情 API
- [ ] 手动重新推送 API
- [ ] 取消待推送任务 API

**API 端点设计**:
- `GET /api/v1/push-tasks/` - 推送历史列表
- `GET /api/v1/push-tasks/{id}` - 推送详情
- `POST /api/v1/push-tasks/{id}/retry` - 重新推送
- `DELETE /api/v1/push-tasks/{id}` - 取消推送

**文件涉及**:
- `app/api/v1/push_tasks.py` - 推送任务 API (新建)
- `app/schemas/push_task.py` - 推送任务 Schema (新建)

**验收标准**:
- ✅ 用户能查看自己的推送历史
- ✅ 失败的推送可以手动重试
- ✅ 待推送任务可以取消

---

## 🎨 阶段 3: 场景模板系统 (1周)

> **目标**: 实现 6 大场景快速创建提醒

### 3.1 模板数据设计 ⭐⭐

**任务清单**:
- [ ] 设计模板数据结构 (JSON)
- [ ] 定义 6 大场景的默认配置
- [ ] 创建模板数据表或 JSON 配置文件
- [ ] 支持模板自定义参数

**6 大场景模板**:

| 场景 | 默认提醒 | 周期配置 | 提前提醒 |
|------|---------|---------|---------|
| 🏠 居住 | 交房租、水电费、物业费 | 每月25号 | 提前1天 |
| 🏥 健康 | 吃药、体检、复查 | 每日/每月 | 提前30分钟 |
| 🐕 宠物 | 疫苗、洗澡、美容 | 每3个月 | 提前3天 |
| 💰 财务 | 信用卡还款、保险续费 | 每月固定日 | 提前3天 |
| 📄 证件 | 身份证、护照续期 | 每年/每10年 | 提前30天 |
| 🎂 纪念 | 生日、纪念日 | 每年固定日 | 提前7天 |

**文件涉及**:
- `app/data/templates.json` - 模板配置 (新建)
- `app/models/template.py` - 模板模型 (可选)
- `app/schemas/template.py` - 模板 Schema (新建)

---

### 3.2 模板 API 实现 ⭐⭐

**任务清单**:
- [ ] 获取所有模板 API
- [ ] 根据模板创建提醒 API
- [ ] 模板搜索和筛选

**API 端点设计**:
- `GET /api/v1/templates/` - 获取模板列表
- `GET /api/v1/templates/{id}` - 模板详情
- `POST /api/v1/reminders/from-template` - 从模板创建提醒

**请求示例**:
```json
{
  "template_id": "rent_monthly",
  "custom_data": {
    "title": "交房租",
    "day": 25,
    "amount": 3000
  }
}
```

**文件涉及**:
- `app/api/v1/templates.py` - 模板 API (新建)
- `app/services/template_service.py` - 模板服务 (新建)

**验收标准**:
- ✅ 用户能查看所有模板
- ✅ 从模板创建提醒成功
- ✅ 自定义参数正确应用

---

## 🚀 阶段 4: 高级功能 (2-3周)

> **目标**: 语音识别、AI 解析、数据分析

### 4.1 语音识别集成 ⭐

**任务清单**:
- [ ] 注册科大讯飞账号获取 API 密钥
- [ ] 集成科大讯飞 ASR SDK
- [ ] 处理音频上传和格式转换
- [ ] 实现实时/离线语音识别
- [ ] 处理识别错误和超时

**文件涉及**:
- `app/services/asr_service.py` - 语音识别服务 (新建)
- `app/api/v1/voice.py` - 语音接口 (新建)

**支持格式**: wav, mp3, pcm

---

### 4.2 AI 意图解析 ⭐⭐

**任务清单**:
- [ ] 注册 DeepSeek API 账号
- [ ] 设计提示词 (Prompt) 模板
- [ ] 实现意图解析函数
- [ ] 提取提醒信息 (标题、时间、周期)
- [ ] 处理解析失败情况

**解析示例**:
- 输入: "每月25号提醒我交房租"
- 输出:
```json
{
  "title": "交房租",
  "category": "rent",
  "recurrence_type": "monthly",
  "recurrence_config": {"day": 25},
  "first_remind_time": "2025-11-25T09:00:00"
}
```

**文件涉及**:
- `app/services/llm_service.py` - LLM 服务 (新建)
- `app/services/intent_parser.py` - 意图解析 (新建)

---

### 4.3 提醒统计分析 ⭐

**任务清单**:
- [ ] 用户提醒完成率统计
- [ ] 提醒分类分布统计
- [ ] 时间分布分析 (按月/周)
- [ ] 生成统计图表数据

**API 端点**:
- `GET /api/v1/statistics/overview` - 总览
- `GET /api/v1/statistics/category` - 分类统计
- `GET /api/v1/statistics/timeline` - 时间轴

**文件涉及**:
- `app/api/v1/statistics.py` - 统计 API (新建)
- `app/services/statistics_service.py` - 统计服务 (新建)

---

## 🧪 阶段 5: 测试和优化 (1-2周)

> **目标**: 完善测试、性能优化、部署准备

### 5.1 单元测试 ⭐⭐⭐

**任务清单**:
- [ ] 安装 pytest 和测试依赖
- [ ] 核心服务单元测试 (周期引擎、推送服务)
- [ ] API 端点集成测试
- [ ] Mock 外部服务 (推送、语音识别)
- [ ] 测试覆盖率报告

**目标覆盖率**:
- 核心服务: > 90%
- API 端点: > 80%
- 总体: > 70%

**文件涉及**:
- `tests/conftest.py` - pytest 配置
- `tests/test_*.py` - 各模块测试

---

### 5.2 性能优化 ⭐⭐

**任务清单**:
- [ ] 数据库查询优化 (添加索引)
- [ ] 实现 Redis 缓存 (用户信息、模板)
- [ ] API 响应时间优化
- [ ] 数据库连接池配置
- [ ] 慢查询日志分析

**优化目标**:
- API 平均响应时间 < 100ms
- 支持 1000 并发用户
- 数据库查询 < 50ms

---

### 5.3 Docker 部署 ⭐⭐

**任务清单**:
- [ ] 编写 Dockerfile
- [ ] 编写 docker-compose.yml (包含 PostgreSQL, Redis)
- [ ] 配置环境变量管理
- [ ] 健康检查和日志配置
- [ ] 编写部署文档

**文件涉及**:
- `Dockerfile` - 应用镜像
- `docker-compose.yml` - 服务编排
- `DEPLOY.md` - 部署文档

---

## 📅 开发时间线

```
Week 1-2:  阶段1 - 核心功能完善
Week 3-4:  阶段2 - 推送系统
Week 5:    阶段3 - 场景模板
Week 6-8:  阶段4 - 高级功能 (可选)
Week 9-10: 阶段5 - 测试和优化
```

---

## 🎯 MVP (最小可行产品) 范围

**必须完成** (6周内):
- ✅ 阶段1: 核心功能完善
- ✅ 阶段2: 推送系统
- ✅ 阶段3: 场景模板
- ✅ 阶段5: 基础测试和部署

**可延后** (V2.0):
- 阶段4: 语音识别和 AI 解析
- 高级统计分析
- 家庭共享功能

---

## 📊 进度跟踪

| 日期 | 阶段 | 完成度 | 备注 |
|------|------|--------|------|
| 2025-11-10 | 框架搭建 | 100% | ✅ 完成 |
| | 阶段1 | 0% | 📋 待开始 |
| | 阶段2 | 0% | 📋 待开始 |
| | 阶段3 | 0% | 📋 待开始 |
| | 阶段4 | 0% | 📋 待开始 |
| | 阶段5 | 0% | 📋 待开始 |

---

## 🚦 下一步行动

**立即开始**: 阶段1.1 - 完善 JWT 认证中间件

1. 打开 `app/core/security.py`
2. 实现 `get_current_user` 函数
3. 测试认证流程
4. 保护 API 端点

**命令**:
```bash
# 激活虚拟环境
.venv\Scripts\activate

# 开始开发
code app/core/security.py
```

---

**准备好了吗？让我们从阶段1开始！** 🚀
