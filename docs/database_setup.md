# 数据库初始化指南

## 步骤 1: 安装 PostgreSQL

### Windows
1. 下载 PostgreSQL: https://www.postgresql.org/download/windows/
2. 运行安装程序，记住设置的密码
3. 默认端口: 5432

### 或使用 Docker (推荐)
```bash
docker run --name timekeeper-postgres -e POSTGRES_PASSWORD=postgres -p 5432:5432 -d postgres:15
```

## 步骤 2: 创建数据库

### 方法 1: 使用 psql 命令行
```bash
# 连接到 PostgreSQL
psql -U postgres

# 创建数据库
CREATE DATABASE timekeeper;

# 退出
\q
```

### 方法 2: 使用 pgAdmin (图形界面)
1. 打开 pgAdmin
2. 右键 Databases → Create → Database
3. 名称: timekeeper
4. 点击 Save

### 方法 3: 使用提供的脚本
```bash
python scripts/init_database.py
```

## 步骤 3: 配置环境变量

编辑 `.env` 文件：

```bash
# 如果使用默认配置
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/timekeeper

# 如果修改了用户名或密码
DATABASE_URL=postgresql://用户名:密码@localhost:5432/timekeeper

# 如果使用 Docker
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/timekeeper
```

## 步骤 4: 运行数据库迁移

```bash
# 激活虚拟环境
.venv\Scripts\activate

# 生成迁移文件
alembic revision --autogenerate -m "Initial tables: users, reminders, push_tasks"

# 执行迁移
alembic upgrade head

# 查看当前版本
alembic current
```

## 步骤 5: 验证数据库

### 使用 psql
```bash
# 连接到数据库
psql -U postgres -d timekeeper

# 查看所有表
\dt

# 查看表结构
\d users
\d reminders
\d push_tasks

# 退出
\q
```

### 使用 Python 脚本
```bash
python scripts/verify_database.py
```

## 常见问题

### 1. 连接失败
- 检查 PostgreSQL 服务是否启动
- 检查端口 5432 是否被占用
- 检查用户名密码是否正确

### 2. 数据库已存在
```bash
# 删除数据库
psql -U postgres -c "DROP DATABASE timekeeper;"

# 重新创建
psql -U postgres -c "CREATE DATABASE timekeeper;"
```

### 3. 迁移失败
```bash
# 查看迁移历史
alembic history

# 回滚到上一版本
alembic downgrade -1

# 删除迁移文件重新生成
rm alembic/versions/*.py
alembic revision --autogenerate -m "Initial"
```

## 下一步

数据库初始化完成后:
1. 启动应用: `python main.py`
2. 访问文档: http://localhost:8000/docs
3. 测试 API 端点
