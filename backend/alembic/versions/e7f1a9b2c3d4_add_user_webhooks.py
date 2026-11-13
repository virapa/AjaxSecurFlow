"""add user_webhooks table for real-time dispatching to external systems

Revision ID: e7f1a9b2c3d4
Revises: c1a4e6f2d8b0
Create Date: 2026-09-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'e7f1a9b2c3d4'
down_revision: Union[str, Sequence[str], None] = 'c1a4e6f2d8b0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'user_webhooks',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('hub_id', sa.String(), nullable=True),
        sa.Column('target_url', sa.String(), nullable=False),
        sa.Column('secret_token', sa.String(), nullable=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    )
    op.create_index(op.f('ix_user_webhooks_id'), 'user_webhooks', ['id'], unique=False)
    op.create_index(op.f('ix_user_webhooks_user_id'), 'user_webhooks', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_webhooks_hub_id'), 'user_webhooks', ['hub_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_user_webhooks_hub_id'), table_name='user_webhooks')
    op.drop_index(op.f('ix_user_webhooks_user_id'), table_name='user_webhooks')
    op.drop_index(op.f('ix_user_webhooks_id'), table_name='user_webhooks')
    op.drop_table('user_webhooks')
