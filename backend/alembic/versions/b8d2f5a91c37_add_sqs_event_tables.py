"""add sqs event tables (ajax_sqs_events, ajax_hub_states, user_hubs)

Revision ID: b8d2f5a91c37
Revises: f41c8abf3f6e
Create Date: 2026-07-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b8d2f5a91c37'
down_revision: Union[str, Sequence[str], None] = 'f41c8abf3f6e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'ajax_sqs_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('message_id', sa.String(), nullable=False),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('hub_id', sa.String(), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('received_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ajax_sqs_events_id'), 'ajax_sqs_events', ['id'], unique=False)
    op.create_index(op.f('ix_ajax_sqs_events_message_id'), 'ajax_sqs_events', ['message_id'], unique=True)
    op.create_index(op.f('ix_ajax_sqs_events_event_type'), 'ajax_sqs_events', ['event_type'], unique=False)
    op.create_index(op.f('ix_ajax_sqs_events_hub_id'), 'ajax_sqs_events', ['hub_id'], unique=False)

    op.create_table(
        'ajax_hub_states',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('hub_id', sa.String(), nullable=False),
        sa.Column('last_event_type', sa.String(), nullable=False),
        sa.Column('last_message_id', sa.String(), nullable=False),
        sa.Column('last_payload', sa.JSON(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ajax_hub_states_id'), 'ajax_hub_states', ['id'], unique=False)
    op.create_index(op.f('ix_ajax_hub_states_hub_id'), 'ajax_hub_states', ['hub_id'], unique=True)

    op.create_table(
        'user_hubs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('hub_id', sa.String(), nullable=False),
        sa.Column('hub_name', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_hubs_id'), 'user_hubs', ['id'], unique=False)
    op.create_index(op.f('ix_user_hubs_user_id'), 'user_hubs', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_hubs_hub_id'), 'user_hubs', ['hub_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_user_hubs_hub_id'), table_name='user_hubs')
    op.drop_index(op.f('ix_user_hubs_user_id'), table_name='user_hubs')
    op.drop_index(op.f('ix_user_hubs_id'), table_name='user_hubs')
    op.drop_table('user_hubs')

    op.drop_index(op.f('ix_ajax_hub_states_hub_id'), table_name='ajax_hub_states')
    op.drop_index(op.f('ix_ajax_hub_states_id'), table_name='ajax_hub_states')
    op.drop_table('ajax_hub_states')

    op.drop_index(op.f('ix_ajax_sqs_events_hub_id'), table_name='ajax_sqs_events')
    op.drop_index(op.f('ix_ajax_sqs_events_event_type'), table_name='ajax_sqs_events')
    op.drop_index(op.f('ix_ajax_sqs_events_message_id'), table_name='ajax_sqs_events')
    op.drop_index(op.f('ix_ajax_sqs_events_id'), table_name='ajax_sqs_events')
    op.drop_table('ajax_sqs_events')
