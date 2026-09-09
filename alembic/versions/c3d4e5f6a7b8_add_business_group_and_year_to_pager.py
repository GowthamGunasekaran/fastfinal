"""Add business_group and year columns to pager table

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-09-09 20:59:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('pager', sa.Column('business_group', sa.String(length=100), nullable=True))
    op.add_column('pager', sa.Column('year', sa.String(length=100), nullable=True))


def downgrade() -> None:
    op.drop_column('pager', 'year')
    op.drop_column('pager', 'business_group')
