"""empty message

Revision ID: 2f37a835bf5e
Revises: 0d3105fb8c2e, 96791dc7d124
Create Date: 2026-01-20 16:35:48.293878

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2f37a835bf5e'
down_revision: Union[str, None] = ('0d3105fb8c2e', '96791dc7d124')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
