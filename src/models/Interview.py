from datetime import datetime
from enum import Enum
from pydantic import BaseModel
from sqlalchemy import ARRAY, JSON, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from models.Base import Base
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import relationship


class InterviewStatus(str, Enum):
    CREATED = "created"
    PREPARING_RESUME = "preparing_resume"
    RESUME_READY = "resume_ready"
    PREPARING_QUESTIONS = "preparing_questions"
    QUESTIONS_READY = "questions_ready"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True)

    question_text = Column(Text, nullable=False)

    category = Column(String(100))
    difficulty = Column(String(50))

    expected_answer = Column(Text)
    skills = Column(ARRAY(String))
    embedding = Column(
        Vector(384)
    )
    question_type = Column(String) # Technical , project , behaviouroul etc
    source = Column(String(100))
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
    resume_embedding = Column(
        Vector(384),
        nullable=True
    )
    status = Column(String(50))
    interview_context = Column(JSONB, nullable = True)
    resume_text = Column(Text, nullable=True)
    resume_summary = Column(Text, nullable=True)
    overall_score = Column(Float, nullable=True)
    overall_summary = Column(Text, nullable=True)
    overall_strengths = Column(JSON, nullable=True)
    overall_gaps = Column(JSON, nullable=True)
    recommendation = Column(Text, nullable=True)
    communication_score = Column(Float, nullable=True)
    technical_score = Column(Float, nullable=True)
    learning_plan = Column(ARRAY(String(255)), nullable=True)
    ai_evaluation = Column(JSONB,nullable=True)
    questions = relationship("InterviewQuestion", back_populates="interview")

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
    original_question = Column(Text)
    personalized_question = Column(Text)
    original_expected_answer = Column(Text)
    # personalized_expected_answer = Column(Text)
    # expected_answer = Column(Text)
    user_answer = Column(Text)
    score = Column(Float)
    feedback = Column(Text)
    assigned_at = Column(
        DateTime,
        default=datetime.utcnow
    )
    strengths = Column(ARRAY(String))
    gaps = Column(ARRAY(String))
    interview = relationship("Interview", back_populates="questions")

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