"""
Add user role field to users table

Revision ID: add_user_role
Revises: add_registration_audit
Create Date: 2025-12-27

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_user_role'
down_revision = 'add_registration_audit'
branch_labels = None
depends_on = None


def upgrade():
    """添加用户角色字段"""
    # 创建枚举类型（PostgreSQL需要）
    # 如果使用MySQL/SQLite，会自动转换为VARCHAR
    op.execute("CREATE TYPE userrole AS ENUM ('USER', 'ADMIN', 'SUPER_ADMIN')")
    
    # 添加角色字段，默认为USER（大写符合Python枚举规范）
    op.add_column('users', 
        sa.Column('role', 
                  sa.Enum('USER', 'ADMIN', 'SUPER_ADMIN', name='userrole'),
                  nullable=False,
                  server_default='USER',
                  comment='用户角色')
    )
    
    # 添加索引
    op.create_index('ix_users_role', 'users', ['role'])


def downgrade():
    """移除用户角色字段"""
    # 删除索引
    op.drop_index('ix_users_role', 'users')
    
    # 删除列
    op.drop_column('users', 'role')
    
    # 删除枚举类型（PostgreSQL）
    op.execute("DROP TYPE IF EXISTS userrole")
