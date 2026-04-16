"""add_social_fields_and_upvotes

Revision ID: f2a1b1c2d3e4
Revises: f1abb6002048
Create Date: 2026-04-14 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f2a1b1c2d3e4'
down_revision: Union[str, Sequence[str], None] = 'f1abb6002048'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add columns to profile_links
    op.add_column('profile_links', sa.Column('category', sa.String(length=32), server_default='OTHER', nullable=False))
    op.add_column('profile_links', sa.Column('canonical_url', sa.Text(), nullable=True))
    op.add_column('profile_links', sa.Column('upvotes', sa.Integer(), server_default='0', nullable=False))
    op.add_column('profile_links', sa.Column('views', sa.Integer(), server_default='0', nullable=False))
    op.add_column('profile_links', sa.Column('is_sponsored', sa.Boolean(), server_default=sa.text('0'), nullable=False))
    op.add_column('profile_links', sa.Column('is_verified', sa.Boolean(), server_default=sa.text('1'), nullable=False))
    op.add_column('profile_links', sa.Column('report_count', sa.Integer(), server_default='0', nullable=False))
    op.add_column('profile_links', sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False))

    # 2. Create user_link_upvotes table
    op.create_table(
        'user_link_upvotes',
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('link_id', sa.BigInteger(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['link_id'], ['profile_links.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'link_id')
    )

    # 3. Create indices
    op.create_index('ix_profile_links_category', 'profile_links', ['category'], unique=False)
    op.create_index('ix_user_link_upvotes_user_link', 'user_link_upvotes', ['user_id', 'link_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_user_link_upvotes_user_link', table_name='user_link_upvotes')
    op.drop_table('user_link_upvotes')
    op.drop_index('ix_profile_links_category', table_name='profile_links')
    op.drop_column('profile_links', 'created_at')
    op.drop_column('profile_links', 'report_count')
    op.drop_column('profile_links', 'is_verified')
    op.drop_column('profile_links', 'is_sponsored')
    op.drop_column('profile_links', 'views')
    op.drop_column('profile_links', 'upvotes')
    op.drop_column('profile_links', 'canonical_url')
    op.drop_column('profile_links', 'category')
