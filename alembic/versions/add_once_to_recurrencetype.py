"""add_once_to_recurrencetype

Revision ID: add_once_recurrence
Revises: 959712c6c00a
Create Date: 2025-12-28

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'add_once_recurrence'
down_revision: Union[str, Sequence[str], None] = '5e24a4ee21c7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Add ONCE to recurrencetype enum."""
    # Get the database connection
    connection = op.get_bind()
    
    # Add ONCE value to the recurrencetype enum
    try:
        # For PostgreSQL, we need to alter the enum type
        connection.execute(sa.text("ALTER TYPE recurrencetype ADD VALUE 'ONCE'"))
    except Exception as e:
        # If it already exists, ignore the error
        print(f"Note: {e}")


def downgrade() -> None:
    """Downgrade schema - Remove ONCE from recurrencetype enum."""
    # Note: PostgreSQL doesn't support removing enum values directly
    # This is a limitation of PostgreSQL
    pass
