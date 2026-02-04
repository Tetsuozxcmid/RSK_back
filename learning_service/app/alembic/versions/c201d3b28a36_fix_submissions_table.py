"""fix_submissions_table

Revision ID: c201d3b28a36
Revises: 2c1d1e568288
Create Date: 2025-10-08 15:31:12.841467

"""

from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "c201d3b28a36"
down_revision: Union[str, None] = "2c1d1e568288"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
