"""Add qr_code column to urls table

Revision ID: 002_add_qr_code_to_urls
Revises: 001_create_urls_table
Create Date: 2026-11-10 18:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '002_add_qr_code_to_urls'
down_revision: Union[str, None] = '001_create_urls_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('urls', sa.Column('qr_code', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('urls', 'qr_code')
