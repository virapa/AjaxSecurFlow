"""add ajax_event_id to ajax_sqs_events for cross-recipient dedup

Revision ID: c1a4e6f2d8b0
Revises: b8d2f5a91c37
Create Date: 2026-07-09

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'c1a4e6f2d8b0'
down_revision: Union[str, Sequence[str], None] = 'b8d2f5a91c37'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('ajax_sqs_events', sa.Column('ajax_event_id', sa.String(), nullable=True))
    op.create_index(op.f('ix_ajax_sqs_events_ajax_event_id'), 'ajax_sqs_events', ['ajax_event_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_ajax_sqs_events_ajax_event_id'), table_name='ajax_sqs_events')
    op.drop_column('ajax_sqs_events', 'ajax_event_id')
