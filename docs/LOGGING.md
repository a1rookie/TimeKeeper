# 日志系统配置文档

## 📋 概述

TimeKeeper使用统一的日志配置系统，所有日志文件存放在 `logs/` 目录下。

## 📁 文件结构

```
TimeKeeper/
├── logs/                       # 日志目录（已加入.gitignore）
│   ├── app.log                # 应用主日志（INFO及以上）
│   ├── app.log.1              # 日志轮转备份1
│   ├── app.log.2              # 日志轮转备份2
│   ├── ...
│   ├── error.log              # 错误日志（ERROR及以上）
│   └── error.log.1            # 错误日志备份
├── app/
│   └── core/
│       └── logging_config.py  # 日志配置模块
└── main.py                    # 启动时初始化日志
```

## ⚙️ 配置位置

**核心配置文件**: `app/core/logging_config.py`

**初始化位置**: `main.py` 第16行

```python
from app.core.logging_config import setup_logging

# 初始化日志系统
setup_logging()
```

## 🎯 日志特性

### 1. 双重输出
- ✅ **控制台输出**：实时查看日志（开发调试）
- ✅ **文件输出**：持久化存储日志（生产环境）

### 2. 日志级别
- **开发环境** (`DEBUG=true`): DEBUG级别（所有日志）
- **生产环境** (`DEBUG=false`): INFO级别（过滤调试日志）

### 3. 自动轮转
- **单文件大小**: 10MB
- **备份数量**: 5个文件
- **编码**: UTF-8
- **旧文件**: 自动添加 `.1`, `.2`, `.3` 后缀

### 4. 双重日志文件
- **app.log**: 记录所有INFO及以上级别日志
- **error.log**: 只记录ERROR及以上级别（便于快速排查错误）

### 5. 第三方库日志降级
```python
# 降低噪音，避免过多无用日志
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
```

## 📝 使用方法

### 在代码中使用日志

```python
import logging

logger = logging.getLogger(__name__)

# 不同级别的日志
logger.debug("调试信息")       # 仅开发环境
logger.info("普通信息")        # 所有环境
logger.warning("警告信息")     # 所有环境
logger.error("错误信息")       # 所有环境，同时写入error.log
logger.critical("严重错误")    # 所有环境，同时写入error.log
```

### 示例

```python
# app/services/my_service.py
import logging

logger = logging.getLogger(__name__)

class MyService:
    def process_data(self, data):
        logger.info(f"开始处理数据: {len(data)} 条记录")
        
        try:
            # 业务逻辑
            result = self._do_process(data)
            logger.info(f"✅ 数据处理成功: {result}")
            return result
        except ValueError as e:
            logger.warning(f"⚠️  数据验证失败: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ 数据处理失败: {e}", exc_info=True)
            raise
```

## 🔧 配置参数

在 `app/core/logging_config.py` 中可调整的参数：

```python
# 日志格式
formatter = logging.Formatter(
    fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# 文件大小限制
maxBytes=10 * 1024 * 1024  # 10MB

# 备份文件数量
backupCount=5  # 保留5个备份
```

## 🎨 日志格式

```
时间戳 - 模块名 - 级别 - 消息内容
│         │       │       └─ 日志消息
│         │       └─────────── DEBUG/INFO/WARNING/ERROR/CRITICAL
│         └─────────────────── 代码模块路径（如 app.api.v1.users）
└───────────────────────────── 2025-11-12 13:50:15
```

示例输出：
```
2025-11-12 13:50:15 - app.core.logging_config - INFO - ✅ Logging system initialized (level: DEBUG)
2025-11-12 13:50:16 - main - INFO - Starting TimeKeeper application...
2025-11-12 13:50:16 - main - INFO - ✅ Session management initialized with Redis
```

## 📊 日志文件管理

### 查看实时日志
```powershell
# PowerShell
Get-Content logs/app.log -Wait -Tail 20

# Linux/Mac
tail -f logs/app.log
```

### 查看错误日志
```powershell
# PowerShell
Get-Content logs/error.log

# Linux/Mac
cat logs/error.log
```

### 清理旧日志（慎用！）
```powershell
# PowerShell - 删除所有日志文件
Remove-Item logs/*.log*

# Linux/Mac
rm logs/*.log*
```

### 查看日志文件大小
```powershell
# PowerShell
Get-ChildItem logs/ -Filter *.log* | Select-Object Name, Length

# Linux/Mac
ls -lh logs/*.log*
```

## 🚀 生产环境建议

### 1. 日志监控
- 使用日志收集工具（如 ELK Stack、Grafana Loki）
- 设置错误日志告警（error.log有新内容时发送通知）

### 2. 日志轮转策略调整
根据实际流量调整参数：
```python
# 高流量应用：更大的文件、更多备份
maxBytes=50 * 1024 * 1024  # 50MB
backupCount=10  # 保留10个备份

# 低流量应用：保持默认
maxBytes=10 * 1024 * 1024  # 10MB
backupCount=5
```

### 3. 日志级别调整
生产环境建议使用 INFO 级别：
```bash
# .env
DEBUG=false  # 自动使用INFO级别
```

### 4. 敏感信息过滤
```python
# 不要记录敏感信息
logger.info(f"用户登录: {phone}")  # ✅ 可以
logger.info(f"密码: {password}")   # ❌ 绝对不可以
logger.info(f"Token: {token}")     # ❌ 绝对不可以
```

## 🐛 常见问题

### Q: 日志文件在哪里？
A: `logs/app.log` 和 `logs/error.log`

### Q: 为什么控制台和文件都有日志？
A: 这是有意设计的。控制台便于开发调试，文件便于生产环境追溯。

### Q: 如何只保留错误日志？
A: 查看 `logs/error.log` 文件，它只包含ERROR及以上级别。

### Q: 日志文件太大怎么办？
A: 系统会自动轮转。当超过10MB时，自动重命名为 `.1`、`.2` 等，保留5个备份。

### Q: 第三方库日志太多？
A: 已在配置中降低了uvicorn和sqlalchemy的日志级别，如需调整其他库：
```python
logging.getLogger("库名").setLevel(logging.WARNING)
```

## 📚 相关文件

- `app/core/logging_config.py` - 日志配置模块
- `main.py` - 日志初始化入口
- `.gitignore` - 排除logs/目录和*.log文件
- `logs/README.md` - 日志目录说明

## ✅ 验证

启动应用后检查：
1. ✅ `logs/` 目录已创建
2. ✅ `logs/app.log` 存在且有内容
3. ✅ `logs/error.log` 存在（可能为空，这是正常的）
4. ✅ 控制台输出日志
5. ✅ 文件中的日志与控制台一致

---

**最后更新**: 2025-11-12  
**维护者**: TimeKeeper Team
