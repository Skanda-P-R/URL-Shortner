"""Create urls table

Revision ID: 001_create_urls_table
Revises: 
Create Date: 2026-11-10 16:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '001_create_urls_table'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'urls',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('original_url', sa.Text(), nullable=False),
        sa.Column('short_code', sa.String(length=16), nullable=False),
        sa.Column('click_count', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_urls_original_url', 'urls', ['original_url'], unique=True)
    op.create_index('idx_urls_short_code', 'urls', ['short_code'], unique=True)


def downgrade() -> None:
    op.drop_index('idx_urls_short_code', table_name='urls')
    op.drop_index('idx_urls_original_url', table_name='urls')
    op.drop_table('urls')
