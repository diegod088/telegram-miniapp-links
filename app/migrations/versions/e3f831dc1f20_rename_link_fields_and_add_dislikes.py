"""rename_link_fields_and_add_dislikes

Revision ID: e3f831dc1f20
Revises: d88a2309343b
Create Date: 2026-04-16 19:58:21.420208

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e3f831dc1f20'
down_revision: Union[str, Sequence[str], None] = 'd88a2309343b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Handle user_link_upvotes -> user_link_likes rename
    op.rename_table('user_link_upvotes', 'user_link_likes')
    with op.batch_alter_table('user_link_likes') as batch_op:
        batch_op.drop_index('ix_user_link_upvotes_user_link')
        batch_op.create_index('ix_user_link_likes_user_link', ['user_id', 'link_id'], unique=False)

    # 2. Create user_link_dislikes
    op.create_table('user_link_dislikes',
    sa.Column('user_id', sa.BigInteger(), nullable=False),
    sa.Column('link_id', sa.BigInteger(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['link_id'], ['profile_links.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('user_id', 'link_id')
    )
    op.create_index('ix_user_link_dislikes_user_link', 'user_link_dislikes', ['user_id', 'link_id'], unique=False)

    # 3. Handle profile_links column renames
    with op.batch_alter_table('profile_links') as batch_op:
        batch_op.add_column(sa.Column('likes', sa.Integer(), server_default='0', nullable=False))
        batch_op.add_column(sa.Column('dislikes', sa.Integer(), server_default='0', nullable=False))
        batch_op.add_column(sa.Column('clicks', sa.Integer(), server_default='0', nullable=False))
        
        # Data migration: Copy upvotes to likes, views to clicks
        # We do this before dropping old columns
    
    op.execute("UPDATE profile_links SET likes = upvotes, clicks = views")

    with op.batch_alter_table('profile_links') as batch_op:
        batch_op.drop_column('upvotes')
        batch_op.drop_column('views')

    # 4. Other auto-detected changes
    with op.batch_alter_table('pending_invoices') as batch_op:
        batch_op.alter_column('status', existing_type=sa.VARCHAR(length=16), nullable=False)
        batch_op.alter_column('created_at', existing_type=sa.DATETIME(), nullable=False)

    with op.batch_alter_table('profiles') as batch_op:
        batch_op.alter_column('boost_until', existing_type=sa.DATETIME(), type_=sa.TIMESTAMP(timezone=True), existing_nullable=True)
        batch_op.alter_column('boost_score', existing_type=sa.FLOAT(), nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Downgrade logic (simplified, ideally mirrors upgrade)
    with op.batch_alter_table('profiles') as batch_op:
        batch_op.alter_column('boost_score', existing_type=sa.FLOAT(), nullable=True)
        batch_op.alter_column('boost_until', existing_type=sa.TIMESTAMP(timezone=True), type_=sa.DATETIME(), existing_nullable=True)

    with op.batch_alter_table('profile_links') as batch_op:
        batch_op.add_column(sa.Column('upvotes', sa.Integer(), server_default='0', nullable=False))
        batch_op.add_column(sa.Column('views', sa.Integer(), server_default='0', nullable=False))
    
    op.execute("UPDATE profile_links SET upvotes = likes, views = clicks")

    with op.batch_alter_table('profile_links') as batch_op:
        batch_op.drop_column('likes')
        batch_op.drop_column('dislikes')
        batch_op.drop_column('clicks')

    op.drop_index('ix_user_link_dislikes_user_link', table_name='user_link_dislikes')
    op.drop_table('user_link_dislikes')

    op.rename_table('user_link_likes', 'user_link_upvotes')
    with op.batch_alter_table('user_link_upvotes') as batch_op:
        batch_op.drop_index('ix_user_link_likes_user_link')
        batch_op.create_index('ix_user_link_upvotes_user_link', ['user_id', 'link_id'], unique=False)
