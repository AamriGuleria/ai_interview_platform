"""mig_03_interview_models

Revision ID: fd131a356252
Revises: 1565b42bcd77
Create Date: 2026-06-05 09:53:46.564063

"""
from typing import Sequence, Union
from sqlalchemy.dialects import postgresql
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fd131a356252'
down_revision: Union[str, Sequence[str], None] = '1565b42bcd77'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():

    op.create_table(
        "questions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=100)),
        sa.Column("difficulty", sa.String(length=50)),
        sa.Column("expected_answer", sa.Text()),
        sa.Column("created_at", sa.DateTime(), nullable=False)
    )

    op.create_table(
        "interviews",
        sa.Column("id", sa.Integer(), primary_key=True),

        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id"),
            nullable=False
        ),

        sa.Column(
            "app_session_id",
            sa.Integer(),
            sa.ForeignKey("app_session.id"),
            nullable=False
        ),

        sa.Column(
            "target_role",
            sa.String(length=255)
        ),

        sa.Column(
            "experience",
            sa.Integer()
        ),

        sa.Column(
            "skills",
            postgresql.ARRAY(sa.String())
        ),

        sa.Column(
            "resume_url",
            sa.String(length=500)
        ),

        sa.Column(
            "started_at",
            sa.DateTime()
        ),

        sa.Column(
            "completed_at",
            sa.DateTime()
        ),

        sa.Column(
            "status",
            sa.String(length=50)
        ),

        sa.Column(
            "interview_context",
            postgresql.JSONB()
        ),

        sa.Column(
            "resume_text",
            sa.Text()
        ),

        sa.Column(
            "resume_summary",
            sa.Text()
        )
    )

    op.create_table(
        "interview_questions",
        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True
        ),

        sa.Column(
            "interview_id",
            sa.Integer(),
            sa.ForeignKey("interviews.id"),
            nullable=False
        ),

        sa.Column(
            "question_id",
            sa.Integer(),
            sa.ForeignKey("questions.id"),
            nullable=False
        ),

        sa.Column(
            "order_no",
            sa.Integer()
        ),

        sa.Column(
            "assigned_at",
            sa.DateTime(),
            nullable=False
        )
    )

    op.create_table(
        "answers",
        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True
        ),

        sa.Column(
            "interview_id",
            sa.Integer(),
            sa.ForeignKey("interviews.id"),
            nullable=False
        ),

        sa.Column(
            "question_id",
            sa.Integer(),
            sa.ForeignKey("questions.id"),
            nullable=False
        ),

        sa.Column(
            "user_answer",
            sa.Text()
        ),

        sa.Column(
            "ai_score",
            sa.Integer()
        ),

        sa.Column(
            "ai_feedback",
            sa.Text()
        ),

        sa.Column(
            "answered_at",
            sa.DateTime(),
            nullable=False
        )
    )

    op.create_index(
        "ix_interviews_user_id",
        "interviews",
        ["user_id"]
    )

    op.create_index(
        "ix_answers_interview_id",
        "answers",
        ["interview_id"]
    )

    op.create_index(
        "ix_answers_question_id",
        "answers",
        ["question_id"]
    )


def downgrade():

    op.drop_index("ix_answers_question_id")
    op.drop_index("ix_answers_interview_id")
    op.drop_index("ix_interviews_user_id")

    op.drop_table("answers")
    op.drop_table("interview_questions")
    op.drop_table("interviews")
    op.drop_table("questions")
