"""change category to string

Revision ID: change_category_to_string
Revises: 7ad7168b373a
Create Date: 2025-12-28 00:00:00.000000

将 reminders 表的 category 字段从枚举类型改为字符串类型，支持用户自定义分类
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'change_category_to_string'
down_revision: Union[str, None] = 'add_once_recurrence'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    将 category 从枚举改为 VARCHAR(50)
    """
    # 1. 添加新的 category_new 列（VARCHAR类型）
    op.add_column('reminders', sa.Column('category_new', sa.String(50), nullable=True))
    
    # 2. 将旧的枚举值转换为字符串并复制到新列
    # SQLite 不支持直接修改枚举类型，需要通过中间列
    op.execute("""
        UPDATE reminders 
        SET category_new = CASE 
            WHEN category = 'RENT' THEN 'rent'
            WHEN category = 'HEALTH' THEN 'health'
            WHEN category = 'PET' THEN 'pet'
            WHEN category = 'FINANCE' THEN 'finance'
            WHEN category = 'DOCUMENT' THEN 'document'
            WHEN category = 'MEMORIAL' THEN 'memorial'
            WHEN category = 'OTHER' THEN 'other'
            ELSE 'other'
        END
    """)
    
    # 3. 删除旧的 category 列
    op.drop_column('reminders', 'category')
    
    # 4. 重命名 category_new 为 category
    op.alter_column('reminders', 'category_new', new_column_name='category', nullable=False)
    
    # 5. 添加索引以提高查询性能
    op.create_index('ix_reminders_category', 'reminders', ['category'])


def downgrade() -> None:
    """
    回滚：将 category 从字符串改回枚举
    """
    # 1. 删除索引
    op.drop_index('ix_reminders_category', 'reminders')
    
    # 2. 添加临时枚举列
    op.add_column('reminders', 
        sa.Column('category_enum', 
                  sa.Enum('RENT', 'HEALTH', 'PET', 'FINANCE', 'DOCUMENT', 'MEMORIAL', 'OTHER', 
                         name='remindercategory'),
                  nullable=True))
    
    # 3. 转换回枚举值（只转换标准分类，自定义分类转为 OTHER）
    op.execute("""
        UPDATE reminders 
        SET category_enum = CASE 
            WHEN category = 'rent' THEN 'RENT'
            WHEN category = 'health' THEN 'HEALTH'
            WHEN category = 'pet' THEN 'PET'
            WHEN category = 'finance' THEN 'FINANCE'
            WHEN category = 'document' THEN 'DOCUMENT'
            WHEN category = 'memorial' THEN 'MEMORIAL'
            ELSE 'OTHER'
        END
    """)
    
    # 4. 删除字符串列
    op.drop_column('reminders', 'category')
    
    # 5. 重命名回 category
    op.alter_column('reminders', 'category_enum', new_column_name='category', nullable=False)
