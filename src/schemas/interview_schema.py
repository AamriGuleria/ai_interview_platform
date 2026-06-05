from typing import List
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