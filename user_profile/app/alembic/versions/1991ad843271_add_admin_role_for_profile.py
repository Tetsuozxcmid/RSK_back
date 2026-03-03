"""add admin role for profile

Revision ID: 1991ad843271
Revises: 93b799778999
Create Date: 2026-03-03 21:13:20.506196

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1991ad843271'
down_revision: Union[str, None] = '93b799778999'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.execute("ALTER TYPE user_role_enum ADD VALUE 'admin'")


def downgrade():
    pass
