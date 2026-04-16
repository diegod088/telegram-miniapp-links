"""Add VIP Boost and Daily limits

Revision ID: d88a2309343b
Revises: f2a1b1c2d3e4
Create Date: 2026-04-15 22:44:11.806076

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'd88a2309343b'
down_revision: Union[str, Sequence[str], None] = 'f2a1b1c2d3e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Adding columns to profile_links
    op.add_column('profile_links', sa.Column('is_premium', sa.Boolean(), nullable=False, server_default=sa.text('0')))
    op.add_column('profile_links', sa.Column('boosted_until', sa.DateTime(), nullable=True))
    
    # Adding columns to users
    op.add_column('users', sa.Column('last_link_created_at', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('daily_link_count', sa.Integer(), nullable=False, server_default=sa.text('0')))
    op.add_column('users', sa.Column('last_reset_date', sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'last_reset_date')
    op.drop_column('users', 'daily_link_count')
    op.drop_column('users', 'last_link_created_at')
    op.drop_column('profile_links', 'boosted_until')
    op.drop_column('profile_links', 'is_premium')
