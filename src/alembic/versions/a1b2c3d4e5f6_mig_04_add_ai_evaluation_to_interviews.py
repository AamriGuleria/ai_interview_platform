"""mig_04_add_ai_evaluation_to_interviews

Revision ID: a1b2c3d4e5f6
Revises: fd131a356252
Create Date: 2026-06-05 10:00:00.000000

"""
from typing import Sequence, Union
from sqlalchemy.dialects import postgresql
from alembic import op
import sqlalchemy as sa

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'fd131a356252'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column(
        'interviews',
        sa.Column('ai_evaluation', postgresql.JSONB(), nullable=True)
    )


def downgrade():
    op.drop_column('interviews', 'ai_evaluation')
