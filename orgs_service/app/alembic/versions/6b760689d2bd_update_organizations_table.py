"""Update organizations table

Revision ID: 6b760689d2bd
Revises: 04606ddc8dea
Create Date: 2026-01-20 18:03:11.427733

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '6b760689d2bd'
down_revision: Union[str, None] = '04606ddc8dea'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Создаем тип enum для PostgreSQL
    org_type_enum = postgresql.ENUM(
        'educational', 
        'medical', 
        'commercial', 
        'governmental',
        name='org_type_enum',
        create_type=True
    )
    org_type_enum.create(op.get_bind(), checkfirst=True)
    
    # Создаем таблицу organizations
    op.create_table('organizations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('full_name', sa.String(), nullable=False),
        sa.Column('short_name', sa.String(), nullable=False),
        sa.Column('kpp', sa.BigInteger(), nullable=False),
        sa.Column('region', sa.String(), nullable=False),
        sa.Column('type', org_type_enum, nullable=False),
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
    
    # Создаем индекс для kpp (опционально, но рекомендуется для уникальных полей)
    op.create_index(op.f('ix_organizations_kpp'), 'organizations', ['kpp'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    # Удаляем таблицу
    op.drop_table('organizations')
    
    # Удаляем тип enum
    org_type_enum = postgresql.ENUM(
        'educational', 
        'medical', 
        'commercial', 
        'governmental',
        name='org_type_enum'
    )
    org_type_enum.drop(op.get_bind())