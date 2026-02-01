"""changed id to uuid

Revision ID: 189d0e01a0b0
Revises: 54392d355c4f
Create Date: 2025-06-15 00:30:43.777404

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "189d0e01a0b0"
down_revision: Union[str, None] = "54392d355c4f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.alter_column(
        "users",
        "id",
        existing_type=sa.INTEGER(),
        type_=sa.INTEGER(),
        autoincrement=True,
    )


def downgrade():
    pass
