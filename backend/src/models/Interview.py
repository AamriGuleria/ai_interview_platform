from datetime import datetime
from pydantic import BaseModel
from sqlalchemy import ARRAY, Column, DateTime, ForeignKey, Integer, String, Text, JSONB
from models.Base import Base


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True)

    question_text = Column(Text, nullable=False)

    category = Column(String(100))
    difficulty = Column(String(50))

    expected_answer = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)

class Interview(Base):
    __tablename__ = "interviews"

    id = Column(Integer, primary_key=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id")
    )

    app_session_id = Column(
        Integer,
        ForeignKey("app_session.id")
    )

    target_role = Column(String(255))

    experience = Column(Integer)

    skills = Column(ARRAY(String))

    resume_url = Column(String(500))

    started_at = Column(DateTime)

    completed_at = Column(DateTime)

    status = Column(String(50))
    interview_context = Column(JSONB, nullable = True)
    resume_text = Column(Text, nullable=True)
    resume_summary = Column(Text, nullable=True)

class InterviewQuestion(Base):
    __tablename__ = "interview_questions"

    id = Column(Integer, primary_key=True)

    interview_id = Column(
        Integer,
        ForeignKey("interviews.id")
    )

    question_id = Column(
        Integer,
        ForeignKey("questions.id")
    )

    order_no = Column(Integer)

    assigned_at = Column(
        DateTime,
        default=datetime.utcnow
    )

class Answer(Base):
    __tablename__ = "answers"

    id = Column(Integer, primary_key=True)

    interview_id = Column(
        Integer,
        ForeignKey("interviews.id")
    )

    question_id = Column(
        Integer,
        ForeignKey("questions.id")
    )

    user_answer = Column(Text)

    ai_score = Column(Integer)

    ai_feedback = Column(Text)

    answered_at = Column(
        DateTime,
        default=datetime.utcnow
    )