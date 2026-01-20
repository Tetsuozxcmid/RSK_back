"""drop_orgs_table

Revision ID: 04606ddc8dea
Revises: 2f37a835bf5e
Create Date: 2026-01-20 16:36:13.286274

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from db.models.org_enum import OrgType  # Импорт Enum


# revision identifiers, used by Alembic.
revision: str = '04606ddc8dea'
down_revision: Union[str, None] = '2f37a835bf5e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Сначала удаляем таблицу
    op.drop_table('organizations')
    # Затем можно удалить enum тип, если он больше не используется
    # op.execute('DROP TYPE IF EXISTS org_type_enum')


def downgrade() -> None:
    """Downgrade schema."""
    op.create_table('organizations',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('full_name', sa.String(), nullable=False),
        sa.Column('short_name', sa.String(), nullable=False),
        sa.Column('kpp', sa.Integer(), nullable=False),
        sa.Column('region', sa.String(), nullable=False),
        sa.Column('type', sa.Enum(OrgType, name='org_type_enum'), nullable=False),
        sa.Column('star', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('knowledge_skills_z', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('knowledge_skills_v', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('digital_env_e', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('data_protection_z', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('data_analytics_d', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('automation_a', sa.Float(), nullable=False, server_default='0.0'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('kpp')
    )