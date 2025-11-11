# 周期提醒APP - AI开发实施指南

# 🤖 AI开发实施指南

> **目标**：基于PRD文档，为AI助手提供清晰的开发实施路线图
> 

---

# 🎯 项目核心定位

## 产品愿景

**打造最简单、最好用的周期提醒工具，让用户轻松管理生活中的重要事件。**

## 核心特点

- **3步设置**：极简操作流程
- **智能提醒**：AI优化提醒时间
- **生活场景化**：6大预设模板
- **多代友好**：特别适合中老年用户

## 差异化优势

- 专注周期提醒（非通用任务管理）
- 语音输入 + 智能解析
- 家庭共享功能
- 多渠道提醒（APP+短信+微信+电话）

---

# 🏗️ 技术架构总览

## 技术栈选择

```jsx
前端：Flutter (iOS + Android 跨平台)
后端：FastAPI + Python
数据库：PostgreSQL (主) + Redis (缓存)
消息队列：RabbitMQ
定时任务：APScheduler
推送服务：个推/极光推送
语音识别：科大讯飞 ASR
大模型：DeepSeek API（成本极低）
云服务：阿里云/腾讯云
```

## 系统分层

```
┌─────────────────────────────────────────┐
│         客户端层 (Flutter App)          │
├─────────────────────────────────────────┤
│         网关层 (Nginx + JWT)            │
├─────────────────────────────────────────┤
│       应用服务层 (FastAPI)              │
│  ┌────────────┐  ┌──────────────────┐   │
│  │ 用户管理   │  │  提醒管理服务    │   │
│  │ 推送服务   │  │  语音识别服务    │   │
│  └────────────┘  └──────────────────┘   │
├─────────────────────────────────────────┤
│    数据层 (PostgreSQL + Redis)          │
└─────────────────────────────────────────┘
```

---

# 📊 核心数据模型

## 关键数据表

### 1. users (用户表)

```sql
id: 用户ID
phone: 手机号
nickname: 昵称
settings: 用户偏好(JSON)
created_at: 创建时间
```

### 2. reminders (提醒表) - 核心表

```sql
id: 提醒ID
user_id: 用户ID
title: 提醒标题
category: 分类 (rent/health/pet/finance等)
recurrence_type: 周期类型 (daily/weekly/monthly/yearly)
recurrence_config: 周期配置 (JSON)
next_remind_time: 下次提醒时间
remind_channels: 提醒渠道 (JSON: ["app", "sms"])
is_active: 是否启用
```

### 3. push_tasks (推送任务表)

```sql
id: 任务ID
reminder_id: 关联提醒
user_id: 用户ID
scheduled_time: 计划推送时间
channels: 推送渠道 (JSON)
status: 状态 (pending/sent/failed)
```

---

# 🎨 核心功能设计

## 1. 快速添加功能

### 语音输入实现

```python
class VoiceInputHandler:
    async def process_voice_input(self, audio_data):
        # 1. ASR 语音转文字
        text = await self.asr_service.recognize(audio_data)
        
        # 2. 大模型解析意图
        parsed_result = await self.llm_service.parse_reminder(
            text, user_context
        )
        
        # 3. 创建提醒
        reminder = await self.create_reminder(parsed_result)
        
        return reminder
```

### 场景模板

- 🏠 **居住类**：交房租、水电费、物业费
- 🏥 **健康类**：吃药提醒、体检、复查
- 🐕 **宠物类**：疫苗、洗澡、美容
- 💰 **财务类**：信用卡还款、保险续费
- 📄 **证件类**：身份证、护照续期
- 🎂 **纪念类**：生日、纪念日

## 2. 智能周期计算

### 周期类型支持

```python
class RecurrenceEngine:
    def calculate_next_time(self, recurrence_type, config, last_time):
        if recurrence_type == 'daily':
            return last_time + timedelta(days=1)
        elif recurrence_type == 'weekly':
            return self._calculate_weekly(config, last_time)
        elif recurrence_type == 'monthly':
            return self._calculate_monthly(config, last_time)
        elif recurrence_type == 'yearly':
            return self._calculate_yearly(config, last_time)
```

### 配置格式示例

```json
{
  "monthly": {"day": 25, "skip_weekend": true},
  "weekly": {"weekdays": [1, 3, 5]},
  "yearly": {"month": 3, "day": 15}
}
```

## 3. 多渠道推送系统

### 推送渠道

- **APP推送**：基础提醒（免费）
- **短信提醒**：重要事项（付费功能）
- **微信提醒**：通过服务号（付费功能）
- **语音电话**：老年用户专用（付费功能）

### 推送调度

```python
class PushScheduler:
    async def schedule_push(self, reminder_id, user_id, channels):
        # 创建推送任务
        task = PushTask(
            reminder_id=reminder_id,
            user_id=user_id,
            channels=channels,
            scheduled_time=next_remind_time
        )
        
        # 加入优先级队列
        await self.queue.put(task)
        
        # Redis 定时任务
        await self.redis.zadd('scheduled_pushes', {
            [task.id](http://task.id): task.scheduled_time.timestamp()
        })
```

---

# 📱 用户界面设计

## 主要页面结构

### 1. 首页 - 提醒列表

- 今日提醒卡片展示
- 倒计时显示
- 大号"+添加"按钮
- 左右滑动切换日期

### 2. 添加页面

- 语音输入 / 手动输入切换
- 6大场景模板快选
- 周期设置（日/周/月/年）
- 提醒方式选择

### 3. 详情页面

- 提醒基本信息
- 历史完成记录
- 编辑/暂停/删除操作

## 关键交互设计

- **极简原则**：3步完成设置
- **大字体**：适配中老年用户
- **语音优先**：突出语音输入入口
- **一键操作**：常用功能单击完成

---

# 🚀 开发实施计划

## MVP版本 (V1.0) - 4周

### 第1周：后端基础

- [ ]  FastAPI项目搭建
- [ ]  数据库设计和迁移
- [ ]  用户注册登录API
- [ ]  JWT认证中间件
- [ ]  基础提醒CRUD API

### 第2周：核心功能

- [ ]  周期计算引擎开发
- [ ]  推送任务调度系统
- [ ]  6大场景模板数据
- [ ]  APP推送集成（个推SDK）

### 第3周：Flutter前端

- [ ]  项目初始化和导航
- [ ]  用户登录注册页面
- [ ]  首页提醒列表
- [ ]  添加/编辑提醒页面
- [ ]  本地推送功能

### 第4周：测试和优化

- [ ]  单元测试编写
- [ ]  集成测试
- [ ]  性能优化
- [ ]  应用商店上架准备

## V2.0增强版 - +6周

- [ ]  语音识别集成
- [ ]  智能意图解析（大模型API）
- [ ]  短信推送功能
- [ ]  微信小程序版本
- [ ]  数据同步功能

## V3.0完整版 - +8周

- [ ]  家庭共享功能
- [ ]  语音电话提醒
- [ ]  智能时间优化
- [ ]  数据统计分析
- [ ]  高级个性化设置

---

# 🎯 AI开发助手指导

## 开发优先级

1. **先做核心功能**：提醒创建、周期计算、推送系统
2. **再做体验优化**：语音输入、智能解析
3. **最后做高级功能**：家庭共享、数据分析

## 技术重点

1. **周期计算算法**：处理各种边界情况（闰年、月末等）
2. **推送可靠性**：多渠道冗余、失败重试机制
3. **用户体验**：3步设置原则、大字体设计
4. **性能优化**：数据库索引、Redis缓存

## 测试要求

- **单元测试覆盖率**：>70%
- **关键功能测试**：周期计算、推送调度
- **用户场景测试**：完整的提醒创建和接收流程
- **性能测试**：支持10万用户并发

## 部署和监控

- **容器化部署**：Docker + Docker Compose
- **监控告警**：推送成功率<95%时告警
- **日志记录**：详细记录用户操作和系统错误
- **数据备份**：每日自动备份数据库

---

**🎉 开发目标：打造国内最好用的周期提醒工具！**

> 💡 **给AI的提示**：开发过程中遇到任何问题，都可以参考这份指南。记住我们的核心原则：简单、可靠、贴心。每个功能都要从用户角度思考，是否真正解决了他们的痛点。
>