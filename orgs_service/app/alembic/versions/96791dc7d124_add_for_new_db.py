"""add for new db

Revision ID: 96791dc7d124
Revises: ca0d622bf58d
Create Date: 2026-01-18 18:42:02.132965

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "96791dc7d124"
down_revision: Union[str, None] = "ca0d622bf58d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Сначала создаём ENUM тип
    org_type_enum = postgresql.ENUM(
        "VUZ",
        "COLLEGE",
        "GBU",
        "SCHOOL",
        "MBU",
        "ANO",
        "FGBU",
        "GAU",
        "PO",
        "OD",
        "GKU",
        "OOO",
        "CHU",
        "AO",
        "MKU",
        "ASSOCIATION",
        "IP",
        name="org_type_enum",
    )
    org_type_enum.create(op.get_bind())

    # Теперь добавляем колонки с этим типом
    op.add_column("organizations", sa.Column("full_name", sa.String(), nullable=True))
    op.add_column("organizations", sa.Column("short_name", sa.String(), nullable=True))
    op.add_column("organizations", sa.Column("inn", sa.Integer(), nullable=True))
    op.add_column("organizations", sa.Column("region", sa.String(), nullable=True))
    op.add_column("organizations", sa.Column("type", org_type_enum, nullable=True))
    op.add_column("organizations", sa.Column("star", sa.Float(), nullable=True))
    op.add_column(
        "organizations", sa.Column("knowledge_skills_z", sa.Float(), nullable=True)
    )
    op.add_column(
        "organizations", sa.Column("knowledge_skills_v", sa.Float(), nullable=True)
    )
    op.add_column(
        "organizations", sa.Column("digital_env_e", sa.Float(), nullable=True)
    )
    op.add_column(
        "organizations", sa.Column("data_protection_z", sa.Float(), nullable=True)
    )
    op.add_column(
        "organizations", sa.Column("data_analytics_d", sa.Float(), nullable=True)
    )
    op.add_column("organizations", sa.Column("automation_a", sa.Float(), nullable=True))
    op.create_unique_constraint(None, "organizations", ["inn"])
    op.drop_column("organizations", "name")


def downgrade() -> None:
    """Downgrade schema."""
    # Удаляем колонки
    op.drop_constraint(None, "organizations", type_="unique")
    op.drop_column("organizations", "automation_a")
    op.drop_column("organizations", "data_analytics_d")
    op.drop_column("organizations", "data_protection_z")
    op.drop_column("organizations", "digital_env_e")
    op.drop_column("organizations", "knowledge_skills_v")
    op.drop_column("organizations", "knowledge_skills_z")
    op.drop_column("organizations", "star")
    op.drop_column("organizations", "type")
    op.drop_column("organizations", "region")
    op.drop_column("organizations", "inn")
    op.drop_column("organizations", "short_name")
    op.drop_column("organizations", "full_name")
    op.add_column(
        "organizations",
        sa.Column("name", sa.VARCHAR(), autoincrement=False, nullable=False),
    )

    # Удаляем ENUM тип
    org_type_enum = postgresql.ENUM(name="org_type_enum")
    org_type_enum.drop(op.get_bind())
