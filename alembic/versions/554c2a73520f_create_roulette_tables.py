import uuid
from datetime import datetime, timezone
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '554c2a73520f'
down_revision: Union[str, Sequence[str], None] = 'ca3e4a942cc5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'chat_roulette_searches',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('profile_id', sa.UUID(as_uuid=True), sa.ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column('priority_interest_ids', sa.ARRAY(sa.UUID(as_uuid=True)), nullable=True),
        sa.Column('search_score', sa.Integer(), nullable=False, default=0),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('search_started_at', sa.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)),
        sa.Column('max_wait_time_minutes', sa.Integer(), nullable=False, default=10),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)),
    )

    op.create_table(
        'chat_roulette_sessions',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('profile1_id', sa.UUID(as_uuid=True), sa.ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column('profile2_id', sa.UUID(as_uuid=True), sa.ForeignKey("profiles.id", ondelete="CASCADE"), nullable=True),
        sa.Column('matched_interest_id', sa.UUID(as_uuid=True), sa.ForeignKey("interests.id", ondelete="SET NULL"), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='WAITING'),
        sa.Column('duration_minutes', sa.Integer(), nullable=False, default=5),
        sa.Column('extension_minutes', sa.Integer(), nullable=True),
        sa.Column('extension_approved_by_profile1', sa.Boolean(), nullable=False, default=False),
        sa.Column('extension_approved_by_profile2', sa.Boolean(), nullable=False, default=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rating_from_1_to_2', sa.Integer(), nullable=True),
        sa.Column('rating_from_2_to_1', sa.Integer(), nullable=True),
        sa.Column('end_reason', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)),
    )

    op.create_index('ix_chat_roulette_searches_profile_id', 'chat_roulette_searches', ['profile_id'])
    op.create_index('ix_chat_roulette_searches_is_active', 'chat_roulette_searches', ['is_active'])

    op.create_index('ix_chat_roulette_sessions_profile1_id', 'chat_roulette_sessions', ['profile1_id'])
    op.create_index('ix_chat_roulette_sessions_profile2_id', 'chat_roulette_sessions', ['profile2_id'])
    op.create_index('ix_chat_roulette_sessions_matched_interest_id', 'chat_roulette_sessions', ['matched_interest_id'])
    op.create_index('ix_chat_roulette_sessions_status', 'chat_roulette_sessions', ['status'])

def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_chat_roulette_sessions_status', table_name='chat_roulette_sessions')
    op.drop_index('ix_chat_roulette_sessions_matched_interest_id', table_name='chat_roulette_sessions')
    op.drop_index('ix_chat_roulette_sessions_profile2_id', table_name='chat_roulette_sessions')
    op.drop_index('ix_chat_roulette_sessions_profile1_id', table_name='chat_roulette_sessions')
    op.drop_index('ix_chat_roulette_searches_is_active', table_name='chat_roulette_searches')
    op.drop_index('ix_chat_roulette_searches_profile_id', table_name='chat_roulette_searches')

    op.drop_table('chat_roulette_sessions')
    op.drop_table('chat_roulette_searches')
