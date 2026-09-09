"""Add business_group and year columns to metadata table

Revision ID: a1b2c3d4e5f6
Revises: 4b67b5287c7a
Create Date: 2026-09-09 20:47:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '4b67b5287c7a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('metadata', sa.Column('business_group', sa.JSON(), nullable=False, server_default='[]'))
    op.add_column('metadata', sa.Column('year', sa.JSON(), nullable=False, server_default='[]'))


def downgrade() -> None:
    op.drop_column('metadata', 'year')
    op.drop_column('metadata', 'business_group')
