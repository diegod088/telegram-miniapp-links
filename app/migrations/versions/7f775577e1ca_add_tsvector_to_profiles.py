"""add tsvector to profiles

Revision ID: 7f775577e1ca
Revises: 5687aa4c41a4
Create Date: 2026-04-18 11:31:18.307187

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7f775577e1ca'
down_revision: Union[str, Sequence[str], None] = '5687aa4c41a4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Convert search_vector to tsvector in Postgres."""
    conn = op.get_bind()
    if conn.dialect.name == "postgresql":
        # 1. Convert column type
        op.execute(
            "ALTER TABLE profiles ALTER COLUMN search_vector TYPE tsvector "
            "USING to_tsvector('spanish', COALESCE(search_vector, ''))"
        )
        
        # 2. Create GIN index
        op.execute(
            "CREATE INDEX ix_profiles_search_vector_gin ON profiles USING gin(search_vector)"
        )
        
        # 3. Create Trigger Function
        op.execute("""
            CREATE OR REPLACE FUNCTION update_profile_search_vector()
            RETURNS trigger AS $$
            BEGIN
              NEW.search_vector := to_tsvector('spanish', 
                COALESCE(NEW.display_name, '') || ' ' || 
                COALESCE(NEW.bio, '') || ' ' || 
                COALESCE(NEW.slug, ''));
              RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
        """)
        
        # 4. Create Trigger
        op.execute("""
            CREATE TRIGGER trg_profile_search_vector
            BEFORE INSERT OR UPDATE ON profiles
            FOR EACH ROW EXECUTE FUNCTION update_profile_search_vector();
        """)


def downgrade() -> None:
    """Downgrade schema: Revert search_vector to TEXT in Postgres."""
    conn = op.get_bind()
    if conn.dialect.name == "postgresql":
        # 1. Drop trigger and function
        op.execute("DROP TRIGGER IF EXISTS trg_profile_search_vector ON profiles")
        op.execute("DROP FUNCTION IF EXISTS update_profile_search_vector")
        
        # 2. Drop index
        op.execute("DROP INDEX IF EXISTS ix_profiles_search_vector_gin")
        
        # 3. Revert column type
        op.execute("ALTER TABLE profiles ALTER COLUMN search_vector TYPE TEXT")
