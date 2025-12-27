"""
Add registration audit fields to users table

Revision ID: add_registration_audit
Revises: 
Create Date: 2025-12-27

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_registration_audit'
down_revision = '959712c6c00a'
branch_labels = None
depends_on = None


def upgrade():
    """添加注册审计字段"""
    # 账号状态字段
    op.add_column('users', sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='true', comment='是否已验证手机号'))
    op.add_column('users', sa.Column('is_banned', sa.Boolean(), nullable=False, server_default='false', comment='是否被封禁'))
    op.add_column('users', sa.Column('ban_reason', sa.String(255), nullable=True, comment='封禁原因'))
    op.add_column('users', sa.Column('banned_at', sa.DateTime(), nullable=True, comment='封禁时间'))
    
    # 注册审计信息
    op.add_column('users', sa.Column('registration_ip', sa.String(50), nullable=True, comment='注册IP地址'))
    op.add_column('users', sa.Column('registration_user_agent', sa.String(500), nullable=True, comment='注册User-Agent'))
    op.add_column('users', sa.Column('registration_source', sa.String(50), nullable=True, comment='注册来源(web/ios/android)'))
    
    # 登录信息
    op.add_column('users', sa.Column('last_login_at', sa.DateTime(), nullable=True, comment='最后登录时间'))
    op.add_column('users', sa.Column('last_login_ip', sa.String(50), nullable=True, comment='最后登录IP'))
    
    # 添加索引
    op.create_index('ix_users_is_banned', 'users', ['is_banned'])
    op.create_index('ix_users_registration_ip', 'users', ['registration_ip'])
    op.create_index('ix_users_created_at', 'users', ['created_at'])


def downgrade():
    """移除注册审计字段"""
    # 删除索引
    op.drop_index('ix_users_created_at', 'users')
    op.drop_index('ix_users_registration_ip', 'users')
    op.drop_index('ix_users_is_banned', 'users')
    
    # 删除列
    op.drop_column('users', 'last_login_ip')
    op.drop_column('users', 'last_login_at')
    op.drop_column('users', 'registration_source')
    op.drop_column('users', 'registration_user_agent')
    op.drop_column('users', 'registration_ip')
    op.drop_column('users', 'banned_at')
    op.drop_column('users', 'ban_reason')
    op.drop_column('users', 'is_banned')
    op.drop_column('users', 'is_verified')
