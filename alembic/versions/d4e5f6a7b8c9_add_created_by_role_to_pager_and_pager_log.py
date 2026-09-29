"""Add created_by_role column to pager and pager_log tables

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-09-29 17:22:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    tables = insp.get_table_names()

    # Add created_by_role to pager table
    columns_pager = [c['name'] for c in insp.get_columns('pager')]
    if 'created_by_role' not in columns_pager:
        op.add_column('pager', sa.Column('created_by_role', sa.String(length=100), nullable=True))

    # Add created_by_role to pager_log table (or create pager_log table if not yet created)
    if 'pager_log' in tables:
        columns_log = [c['name'] for c in insp.get_columns('pager_log')]
        if 'created_by_role' not in columns_log:
            op.add_column('pager_log', sa.Column('created_by_role', sa.String(length=100), nullable=True))
    else:
        op.create_table(
            'pager_log',
            sa.Column('pager_log_id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('pager_id', sa.String(length=36), nullable=False),
            sa.Column('created_by', sa.String(length=255), nullable=True),
            sa.Column('created_by_role', sa.String(length=100), nullable=True),
            sa.Column('last_updated_by', sa.String(length=255), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('last_modified_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('action', sa.String(length=50), nullable=False),
            sa.Column('payload', sa.JSON(), nullable=True),
            sa.PrimaryKeyConstraint('pager_log_id'),
        )
        op.create_index('ix_pager_log_pager_id', 'pager_log', ['pager_id'], unique=False)
        op.create_index('ix_pager_log_last_updated_by', 'pager_log', ['last_updated_by'], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    tables = insp.get_table_names()

    if 'pager_log' in tables:
        columns_log = [c['name'] for c in insp.get_columns('pager_log')]
        if 'created_by_role' in columns_log:
            op.drop_column('pager_log', 'created_by_role')

    if 'pager' in tables:
        columns_pager = [c['name'] for c in insp.get_columns('pager')]
        if 'created_by_role' in columns_pager:
            op.drop_column('pager', 'created_by_role')
