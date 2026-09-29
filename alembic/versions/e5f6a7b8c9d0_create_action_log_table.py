"""Create user tracking tables: action_log, login_log, user_details

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-09-29 17:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    tables = insp.get_table_names()

    # 1. action_log table (without foreign keys)
    if 'action_log' not in tables:
        op.create_table(
            'action_log',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('pager_id', sa.String(length=36), nullable=True),
            sa.Column('user_email', sa.String(length=255), nullable=True),
            sa.Column('role', sa.String(length=100), nullable=True),
            sa.Column('market', sa.String(length=100), nullable=True),
            sa.Column('date_time', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
            sa.Column('action', sa.String(length=100), nullable=True),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_action_log_pager_id', 'action_log', ['pager_id'], unique=False)

    # 2. login_log table
    if 'login_log' not in tables:
        op.create_table(
            'login_log',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('user_email', sa.String(length=255), nullable=True),
            sa.Column('role', sa.String(length=100), nullable=True),
            sa.Column('login_time', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
        )

    # 3. user_details table
    if 'user_details' not in tables:
        op.create_table(
            'user_details',
            sa.Column('email', sa.String(length=255), nullable=False),
            sa.Column('role', sa.String(length=100), nullable=True),
            sa.Column('market', sa.String(length=100), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
            sa.Column('last_updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
            sa.PrimaryKeyConstraint('email'),
        )


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    tables = insp.get_table_names()

    if 'user_details' in tables:
        op.drop_table('user_details')

    if 'login_log' in tables:
        op.drop_table('login_log')

    if 'action_log' in tables:
        op.drop_index('ix_action_log_pager_id', table_name='action_log')
        op.drop_table('action_log')
