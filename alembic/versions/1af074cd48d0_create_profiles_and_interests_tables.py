import uuid
from datetime import datetime, timezone
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '1af074cd48d0'
down_revision: Union[str, Sequence[str], None] = '70c3f192b2e8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('interests',
        sa.Column('id', sa.UUID(as_uuid=True), nullable=False, primary_key=True, default=uuid.uuid4),
        sa.Column('name', sa.String(length=40), nullable=False, unique=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table('profiles',
        sa.Column('id', sa.UUID(as_uuid=True), nullable=False, primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('username', sa.String(length=40), nullable=False, unique=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('reputation_score', sa.Float(), nullable=False, default=5.0),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table('profile_interests',
        sa.Column('profile_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('interest_id', sa.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['interest_id'], ['interests.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['profile_id'], ['profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('profile_id', 'interest_id')
    )
    
    op.create_index(op.f('profiles_reputation_score'), 'profiles', ['reputation_score'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('profiles_reputation_score'), table_name='profiles')
    
    op.drop_table('profile_interests')
    op.drop_table('profiles')
    op.drop_table('interests')
