"""add group and language fields

Revision ID: eafc2a8f4918
Revises: 7f775577e1ca
Create Date: 2026-04-18 11:37:04.828981

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'eafc2a8f4918'
down_revision: Union[str, Sequence[str], None] = '7f775577e1ca'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Add group and language fields."""
    op.add_column('profiles', sa.Column('language', sa.String(length=8), nullable=True))
    op.add_column('profiles', sa.Column('telegram_group_url', sa.Text(), nullable=True))
    op.add_column('profiles', sa.Column('member_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('profile_links', sa.Column('thumbnail_url', sa.Text(), nullable=True))
    op.create_index('ix_profiles_language', 'profiles', ['language'], unique=False)


def downgrade() -> None:
    """Downgrade schema: Remove group and language fields."""
    op.drop_index('ix_profiles_language', table_name='profiles')
    op.drop_column('profile_links', 'thumbnail_url')
    op.drop_column('profiles', 'member_count')
    op.drop_column('profiles', 'telegram_group_url')
    op.drop_column('profiles', 'language')
