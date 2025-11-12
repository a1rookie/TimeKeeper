# 🎯 日志系统快速参考

## 📁 位置
```
logs/
├── app.log      # 所有日志
└── error.log    # 只有错误
```

## 🔧 配置文件
`app/core/logging_config.py`

## 📝 使用
```python
import logging
logger = logging.getLogger(__name__)

logger.info("✅ 成功")
logger.warning("⚠️  警告")
logger.error("❌ 错误")
```

## 👀 查看日志
```powershell
# 实时查看
Get-Content logs/app.log -Wait -Tail 20

# 查看错误
Get-Content logs/error.log
```

## ⚙️ 特性
- ✅ 自动轮转（10MB/文件）
- ✅ 保留5个备份
- ✅ UTF-8编码
- ✅ 控制台+文件双输出
- ✅ 开发/生产环境自动切换

## 📚 完整文档
见 `docs/LOGGING.md`
