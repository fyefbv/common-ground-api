from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '3dbef3c9af77'
down_revision: Union[str, Sequence[str], None] = '1af074cd48d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column('interests', 'name',
                    new_column_name='name_translations',
                    existing_type=sa.String(length=40),
                    type_=postgresql.JSONB(),
                    existing_nullable=False,
                    nullable=False,
                    postgresql_using='name::jsonb')

def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('interests', 'name_translations',
                    new_column_name='name',
                    existing_type=postgresql.JSONB(),
                    type_=sa.String(length=40),
                    existing_nullable=False,
                    nullable=False)
