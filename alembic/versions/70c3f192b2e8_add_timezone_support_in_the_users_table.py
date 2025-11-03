from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '70c3f192b2e8'
down_revision: Union[str, Sequence[str], None] = 'f94dadc54c7c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column('users', 'created_at',
                    existing_type=sa.TIMESTAMP(),
                    type_=postgresql.TIMESTAMP(timezone=True),
                    existing_nullable=False)
    op.alter_column('users', 'updated_at',
                    existing_type=sa.TIMESTAMP(),
                    type_=postgresql.TIMESTAMP(timezone=True),
                    existing_nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('users', 'created_at',
                    existing_type=postgresql.TIMESTAMP(timezone=True),
                    type_=sa.TIMESTAMP(),
                    existing_nullable=False)
    op.alter_column('users', 'updated_at',
                    existing_type=postgresql.TIMESTAMP(timezone=True),
                    type_=sa.TIMESTAMP(),
                    existing_nullable=False)
