"""add cascade delete to foreign keys

Revision ID: b96bcdefd58e
Revises: 7bc872c04f07
Create Date: 2026-03-05 18:07:22.762425

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa



revision: str = 'b96bcdefd58e'
down_revision: Union[str, None] = '7bc872c04f07'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
  
    op.drop_constraint('submissions_course_id_fkey', 'submissions', type_='foreignkey')
    op.drop_constraint('user_progress_course_id_fkey', 'user_progress', type_='foreignkey')
    

    op.create_foreign_key(
        'submissions_course_id_fkey',
        'submissions', 'courses',
        ['course_id'], ['id'],
        ondelete='CASCADE'
    )
    op.create_foreign_key(
        'user_progress_course_id_fkey',
        'user_progress', 'courses',
        ['course_id'], ['id'],
        ondelete='CASCADE'
    )


def downgrade() -> None:

    op.drop_constraint('submissions_course_id_fkey', 'submissions', type_='foreignkey')
    op.drop_constraint('user_progress_course_id_fkey', 'user_progress', type_='foreignkey')
    
    op.create_foreign_key(
        'submissions_course_id_fkey',
        'submissions', 'courses',
        ['course_id'], ['id']
    )
    op.create_foreign_key(
        'user_progress_course_id_fkey',
        'user_progress', 'courses',
        ['course_id'], ['id']
    )