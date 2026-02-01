"""add_moder_to_enum_manual

Revision ID: a4316195a7fe
Revises: d072bb4d8db5
Create Date: 2025-11-13 12:40:40.774246

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "a4316195a7fe"
down_revision: Union[str, None] = "d072bb4d8db5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE user_role_enum ADD VALUE 'MODER'")


def downgrade() -> None:
    """Downgrade schema."""
    pass
