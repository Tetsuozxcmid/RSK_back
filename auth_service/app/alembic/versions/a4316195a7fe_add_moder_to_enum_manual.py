"""add_moder_to_enum_manual

Revision ID: a4316195a7fe
Revises: d701ece7034c
Create Date: 2025-11-13 12:40:40.774246

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a4316195a7fe'
down_revision: Union[str, None] = 'd701ece7034c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.execute("ALTER TYPE user_role_enum ADD VALUE 'MODER'")


def downgrade() -> None:
    """Downgrade schema."""
    pass
