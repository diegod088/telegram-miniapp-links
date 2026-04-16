"""add_featured_flag_to_profilelinks

Revision ID: 5687aa4c41a4
Revises: e3f831dc1f20
Create Date: 2026-04-16 20:16:59.898121

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5687aa4c41a4'
down_revision: Union[str, Sequence[str], None] = 'e3f831dc1f20'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # SQLite friendly column addition with default value 0 (False)
    op.add_column('profile_links', sa.Column('is_featured', sa.Boolean(), nullable=False, server_default=sa.text('0')))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('profile_links') as batch_op:
        batch_op.drop_column('is_featured')
