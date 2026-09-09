"""Add week_start_number and week_end_number columns to pillar_initiative table

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-09-09 20:54:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('pillar_initiative', sa.Column('week_start_number', sa.String(length=20), nullable=True))
    op.add_column('pillar_initiative', sa.Column('week_end_number', sa.String(length=20), nullable=True))


def downgrade() -> None:
    op.drop_column('pillar_initiative', 'week_end_number')
    op.drop_column('pillar_initiative', 'week_start_number')
