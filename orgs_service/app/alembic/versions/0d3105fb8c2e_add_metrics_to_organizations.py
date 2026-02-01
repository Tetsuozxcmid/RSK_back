"""add metrics to organizations

Revision ID: 0d3105fb8c2e
Revises: ca0d622bf58d
Create Date: 2026-01-18 22:22:48.853425

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0d3105fb8c2e"
down_revision: Union[str, None] = "ca0d622bf58d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1) ENUM type (для Postgres это обязательно)
    org_type_enum = sa.Enum(
        "ВУЗ",
        "Колледж",
        "ГБУ",
        "Школа",
        "МБУ",
        "АНО",
        "ФГБУ",
        "ГАУ",
        "ПО",
        "ОД",
        "ГКУ",
        "ООО",
        "ЧУ",
        "АО",
        "МКУ",
        "АССОЦИАЦИЯ",
        "ИП",
        name="org_type_enum",
    )
    org_type_enum.create(op.get_bind(), checkfirst=True)

    # 2) table
    op.create_table(
        "organizations",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("full_name", sa.String(), nullable=False),
        sa.Column("short_name", sa.String(), nullable=False),
        sa.Column("kpp", sa.Integer(), nullable=False, unique=True),
        sa.Column("region", sa.String(), nullable=False),
        sa.Column("type", org_type_enum, nullable=False),
        sa.Column("star", sa.Float(), nullable=False, server_default=sa.text("0.0")),
        sa.Column(
            "knowledge_skills_z",
            sa.Float(),
            nullable=False,
            server_default=sa.text("0.0"),
        ),
        sa.Column(
            "knowledge_skills_v",
            sa.Float(),
            nullable=False,
            server_default=sa.text("0.0"),
        ),
        sa.Column(
            "digital_env_e", sa.Float(), nullable=False, server_default=sa.text("0.0")
        ),
        sa.Column(
            "data_protection_z",
            sa.Float(),
            nullable=False,
            server_default=sa.text("0.0"),
        ),
        sa.Column(
            "data_analytics_d",
            sa.Float(),
            nullable=False,
            server_default=sa.text("0.0"),
        ),
        sa.Column(
            "automation_a", sa.Float(), nullable=False, server_default=sa.text("0.0")
        ),
    )


def downgrade() -> None:
    # 1) drop table
    op.drop_table("organizations")

    # 2) drop enum
    org_type_enum = sa.Enum(name="org_type_enum")
    org_type_enum.drop(op.get_bind(), checkfirst=True)
