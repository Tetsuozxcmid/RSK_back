"""add admin role

Revision ID: 1037e729ff1a
Revises: ddde79c77f6d
Create Date: 2026-03-03 20:35:29.145341

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "1037e729ff1a"
down_revision: Union[str, None] = "ddde79c77f6d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.execute("ALTER TYPE user_role_enum ADD VALUE 'admin'")


def downgrade():
    pass
