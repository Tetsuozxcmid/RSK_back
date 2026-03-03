"""add admin role for profile second

Revision ID: 20bc1a4e634b
Revises: 1991ad843271
Create Date: 2026-03-03 21:19:17.850402

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20bc1a4e634b'
down_revision: Union[str, None] = '93b799778999'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.execute("ALTER TYPE userenum ADD VALUE 'admin'")


def downgrade():
    pass
