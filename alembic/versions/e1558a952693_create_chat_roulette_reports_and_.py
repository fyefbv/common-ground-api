import uuid
from datetime import datetime, timezone
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'e1558a952693'
down_revision: Union[str, Sequence[str], None] = '554c2a73520f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'chat_roulette_reports',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('session_id', sa.UUID(as_uuid=True), sa.ForeignKey("chat_roulette_sessions.id", ondelete="CASCADE")),
        sa.Column('reporter_profile_id', sa.UUID(as_uuid=True), sa.ForeignKey("profiles.id", ondelete="CASCADE")),
        sa.Column('reported_profile_id', sa.UUID(as_uuid=True), sa.ForeignKey("profiles.id", ondelete="CASCADE")),
        sa.Column('reason', sa.String(length=100)),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)),
    )

    op.create_table(
        'chat_roulette_messages',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('session_id', sa.UUID(as_uuid=True), sa.ForeignKey("chat_roulette_sessions.id", ondelete="CASCADE")),
        sa.Column('sender_profile_id', sa.UUID(as_uuid=True), sa.ForeignKey("profiles.id", ondelete="CASCADE")),
        sa.Column('content', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)),
    )

    op.create_index('ix_chat_roulette_reports_session_id', 'chat_roulette_reports', ['session_id'])
    op.create_index('ix_chat_roulette_messages_session_id', 'chat_roulette_messages', ['session_id'])

def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_chat_roulette_messages_session_id', table_name='chat_roulette_messages')
    op.drop_index('ix_chat_roulette_reports_session_id', table_name='chat_roulette_reports')

    op.drop_table('chat_roulette_messages')
    op.drop_table('chat_roulette_reports')
