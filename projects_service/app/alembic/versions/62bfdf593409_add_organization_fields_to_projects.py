"""add organization fields to projects

Revision ID: 62bfdf593409
Revises: 7d43da4d32c7
Create Date: 2026-02-16 21:54:38.465948

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '62bfdf593409'
down_revision: Union[str, Sequence[str], None] = '7d43da4d32c7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('projects', sa.Column('organization_id', sa.Integer(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('projects', 'organization_id')
    