"""add_moder_to_enum_manual_profile

Revision ID: 93b799778999
Revises: 88b6bbbd3677
Create Date: 2025-11-13 15:56:15.325349

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '93b799778999'
down_revision: Union[str, None] = '88b6bbbd3677'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE user_role_enum ADD VALUE 'MODER'")


def downgrade() -> None:
    """Downgrade schema."""
    pass
