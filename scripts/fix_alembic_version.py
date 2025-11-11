"""Check and fix alembic version"""
from app.core.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    # 查看当前版本
    result = conn.execute(text('SELECT * FROM alembic_version'))
    rows = [row for row in result]
    print(f"Current version: {rows}")
    
    # 更新为正确版本
    conn.execute(text("UPDATE alembic_version SET version_num = 'a44df02083fd'"))
    conn.commit()
    print("Version updated to a44df02083fd")
    
    # 确认
    result = conn.execute(text('SELECT * FROM alembic_version'))
    rows = [row for row in result]
    print(f"New version: {rows}")
