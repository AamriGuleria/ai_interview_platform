from typing import Any, Dict, List
from pydantic import BaseModel


class Project(BaseModel):
    name: str
    description: str
    technologies: List[str]

class WorkExperience(BaseModel):
    company: str
    role: str
    duration: str
    responsibilities: List[str]

class ResumeContext(BaseModel):
    candidate_name: str
    years_of_experience: int

    skills: List[str]

    projects: List[Project]

    work_experience: List[WorkExperience]

    education: List[str]

    strength_areas: List[str]

    recommended_topics: List[str]

    difficulty_level: str
    resume_summary: str

class QuestionMetadata(BaseModel):
    category: str
    difficulty: str
    skills: List[str]
    question_type: str

class QuestionMetadataItem(BaseModel):
    id: int
    category: str
    difficulty: str
    skills: List[str]
    question_type: str


class QuestionMetadataBatch(BaseModel):
    questions: List[QuestionMetadataItem]


class PersonalizedQuestion(BaseModel):
    id: int
    personalized_question: str
    personalized_expected_answer: str

class PersonalizedQuestionBatch(BaseModel):
    questions: list[PersonalizedQuestion]

class EvaluationResult(BaseModel):
    score: float
    feedback: str
    strengths: List[str]
    gaps: List[str]

class EvaluationResultBatch(BaseModel):
    results: List[EvaluationResult]

class InterviewResponse(BaseModel):
    overall_score: float
    technical_score: float
    communication_score: float
    overall_summary: str
    overall_strengths: list[str]
    overall_gaps: list[str]
    recommendation: str
    learning_plan: list[str]

class InterviewResponseBatch(BaseModel):
    results: list[InterviewResponse]