import uuid
from datetime import datetime, timezone
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'ca3e4a942cc5'
down_revision: Union[str, Sequence[str], None] = 'd7627c98ded5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "rooms",
        sa.Column("id", sa.UUID(as_uuid=True), nullable=False, primary_key=True, default=uuid.uuid4),
        sa.Column("name", sa.String(length=100), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("primary_interest_id", sa.UUID(as_uuid=True), nullable=True),
        sa.Column("creator_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("tags", sa.ARRAY(sa.String(length=50)), nullable=False),
        sa.Column("max_participants", sa.Integer(), nullable=False),
        sa.Column("is_private", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)),
        sa.ForeignKeyConstraint(
            ["creator_id"],
            ["profiles.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["primary_interest_id"],
            ["interests.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "room_participants",
        sa.Column("room_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("profile_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False, server_default="MEMBER"),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)),
        sa.Column("is_muted", sa.Boolean(), nullable=False),
        sa.Column("is_banned", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["profile_id"],
            ["profiles.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["room_id"],
            ["rooms.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("room_id", "profile_id"),
    )

    op.create_table(
        "room_messages",
        sa.Column("id", sa.UUID(as_uuid=True), nullable=False, primary_key=True, default=uuid.uuid4),
        sa.Column("room_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("sender_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("parent_message_id", sa.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)),
        sa.Column("is_edited", sa.Boolean(), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["parent_message_id"],
            ["room_messages.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["room_id"],
            ["rooms.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["sender_id"],
            ["profiles.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    
    op.create_index(op.f("ix_rooms_creator_id"), "rooms", ["creator_id"], unique=False)
    op.create_index(op.f("ix_rooms_is_private"), "rooms", ["is_private"], unique=False)
    op.create_index(op.f("ix_rooms_primary_interest_id"), "rooms", ["primary_interest_id"], unique=False)
    op.create_index(op.f("ix_rooms_tags"), "rooms", ["tags"], unique=False)

    op.create_index(op.f("ix_room_messages_room_id"), "room_messages", ["room_id"], unique=False)
    op.create_index(op.f("ix_room_messages_sender_id"), "room_messages", ["sender_id"], unique=False)

    op.create_index('ix_room_participants_role', 'room_participants', ['role'])

def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_room_participants_role', table_name='room_participants')
    op.drop_index(op.f("ix_room_messages_sender_id"), table_name="room_messages")
    op.drop_index(op.f("ix_room_messages_room_id"), table_name="room_messages")
    op.drop_index(op.f("ix_rooms_tags"), table_name="rooms")
    op.drop_index(op.f("ix_rooms_primary_interest_id"), table_name="rooms")
    op.drop_index(op.f("ix_rooms_is_private"), table_name="rooms")
    op.drop_index(op.f("ix_rooms_creator_id"), table_name="rooms")

    op.drop_table("room_messages")
    op.drop_table("room_participants")
    op.drop_table("rooms")
