"""fix user_progress

Revision ID: 0783a392ef99
Revises: c201d3b28a36
Create Date: 2025-10-08 15:35:26.547078

"""

from typing import Sequence, Union



# revision identifiers, used by Alembic.
revision: str = "0783a392ef99"
down_revision: Union[str, None] = "c201d3b28a36"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
