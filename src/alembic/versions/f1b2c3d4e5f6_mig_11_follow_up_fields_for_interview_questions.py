from alembic import op
import sqlalchemy as sa

revision = 'f1b2c3d4e5f6'
down_revision = '8cba4ff3a2b0'  # replace with the latest revision if needed
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('interview_questions', sa.Column('follow_up_requested', sa.Boolean(), nullable=True, server_default=sa.false()))
    op.add_column('interview_questions', sa.Column('is_follow_up', sa.Boolean(), nullable=True, server_default=sa.false()))
    op.add_column('interview_questions', sa.Column('parent_question_id', sa.Integer(), nullable=True))
    op.add_column('interview_questions', sa.Column('display_order', sa.Float(), nullable=True, server_default='0'))
    op.create_foreign_key(None, 'interview_questions', 'interview_questions', ['parent_question_id'], ['id'])


def downgrade():
    op.drop_constraint(None, 'interview_questions', type_='foreignkey')
    op.drop_column('interview_questions', 'display_order')
    op.drop_column('interview_questions', 'parent_question_id')
    op.drop_column('interview_questions', 'is_follow_up')
    op.drop_column('interview_questions', 'follow_up_requested')
