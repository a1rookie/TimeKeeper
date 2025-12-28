"""Fix UserRole enum values to uppercase

Revision ID: 5e24a4ee21c7
Revises: add_user_role
Create Date: 2025-12-28 15:14:52.679172

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5e24a4ee21c7'
down_revision: Union[str, Sequence[str], None] = 'add_user_role'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    修复 UserRole ENUM 值为大写
    - 创建临时列存储当前值
    - 删除旧 ENUM 类型
    - 重建大写 ENUM 类型
    - 恢复数据为大写
    """
    # 创建临时列
    op.add_column('users', sa.Column('role_temp', sa.String(20), nullable=True))
    
    # 复制现有值并转换为大写
    op.execute("UPDATE users SET role_temp = UPPER(role::text)")
    
    # 删除旧列（会自动删除旧ENUM类型的引用）
    op.drop_column('users', 'role')
    
    # 删除旧ENUM类型
    op.execute("DROP TYPE IF EXISTS userrole CASCADE")
    
    # 创建新的ENUM类型（使用大写值）
    op.execute("CREATE TYPE userrole AS ENUM ('USER', 'ADMIN', 'SUPER_ADMIN')")
    
    # 重新添加 role 列（使用新ENUM类型和大写值）
    op.add_column('users', 
        sa.Column('role', 
                  sa.Enum('USER', 'ADMIN', 'SUPER_ADMIN', name='userrole'),
                  nullable=False,
                  server_default='USER')
    )
    
    # 恢复数据为大写ENUM值
    op.execute("UPDATE users SET role = role_temp::userrole")
    
    # 清理临时列
    op.drop_column('users', 'role_temp')
    
    # 重建索引
    op.create_index('ix_users_role', 'users', ['role'])


def downgrade() -> None:
    """
    回滚到原始小写ENUM值
    """
    # 删除索引
    op.drop_index('ix_users_role', 'users')
    
    # 创建临时列
    op.add_column('users', sa.Column('role_temp', sa.String(20), nullable=True))
    
    # 复制值到临时列
    op.execute("UPDATE users SET role_temp = role::text")
    
    # 删除role列
    op.drop_column('users', 'role')
    
    # 删除大写ENUM类型
    op.execute("DROP TYPE IF EXISTS userrole CASCADE")
    
    # 创建原始小写ENUM类型
    op.execute("CREATE TYPE userrole AS ENUM ('user', 'admin', 'super_admin')")
    
    # 重新添加role列（使用小写ENUM值）
    op.add_column('users', 
        sa.Column('role', 
                  sa.Enum('user', 'admin', 'super_admin', name='userrole'),
                  nullable=False,
                  server_default='user')
    )
    
    # 恢复数据
    op.execute("UPDATE users SET role = role_temp::userrole")
    
    # 清理临时列
    op.drop_column('users', 'role_temp')
    
    # 重建索引
    op.create_index('ix_users_role', 'users', ['role'])
